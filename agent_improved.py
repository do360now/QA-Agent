"""
IMPROVED Testing Agent - Better loop detection and navigation handling
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import hashlib
import json

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from config import Config
from shared_state import SharedState
from llm_interface_improved import LLMInterface  # Use improved version
from page_analyzer import PageAnalyzer

logger = logging.getLogger(__name__)


class TestingAgent:
    """Autonomous testing agent that explores web applications - IMPROVED"""
    
    def __init__(self, agent_id: int, config: Config, shared_state: SharedState):
        self.agent_id = agent_id
        self.config = config
        self.shared_state = shared_state
        self.llm = LLMInterface(config)
        self.page_analyzer = PageAnalyzer(config)
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        self.actions_taken = 0
        self.pages_visited = set()
        self.findings: List[Dict] = []
        self.current_url = ""
        self.stuck_counter = 0  # Track how many times we've been on same page
        
        self.logger = logging.getLogger(f"Agent-{agent_id}")
    
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()
        
        browser_type = getattr(playwright, self.config.browser_type)
        self.browser = await browser_type.launch(
            headless=self.config.headless
        )
        
        self.context = await self.browser.new_context(
            viewport={
                'width': self.config.viewport_width,
                'height': self.config.viewport_height
            },
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Enable console message and error tracking
        self.page = await self.context.new_page()
        
        # Track JavaScript errors
        if self.config.detect_js_errors:
            self.page.on('pageerror', lambda err: self._handle_js_error(err))
        
        # Track console errors
        self.page.on('console', lambda msg: self._handle_console_message(msg))
        
        # Track network failures
        if self.config.detect_http_errors:
            self.page.on('response', lambda resp: self._handle_response(resp))
        
        self.logger.info("Browser initialized")
    
    async def authenticate(self):
        """Authenticate if credentials provided"""
        if not self.config.auth_username or not self.config.auth_password:
            return
        
        self.logger.info("Attempting authentication...")
        
        try:
            await self.page.goto(self.config.base_url, wait_until='networkidle', timeout=30000)
            
            # Try each username selector until one works
            for selector in self.config.auth_form_selectors['username']:
                try:
                    await self.page.fill(selector, self.config.auth_username, timeout=2000)
                    break
                except:
                    continue
            
            # Try each password selector
            for selector in self.config.auth_form_selectors['password']:
                try:
                    await self.page.fill(selector, self.config.auth_password, timeout=2000)
                    break
                except:
                    continue
            
            # Try each submit selector
            for selector in self.config.auth_form_selectors['submit']:
                try:
                    await self.page.click(selector, timeout=2000)
                    break
                except:
                    continue
            
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            self.logger.info("Authentication successful")
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
    
    async def explore(self, duration_minutes: int):
        """Main exploration loop - IMPROVED"""
        self.logger.info(f"Starting exploration for {duration_minutes} minutes")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        try:
            await self.initialize_browser()
            await self.authenticate()
            
            # Start at base URL
            await self.page.goto(self.config.base_url, wait_until='networkidle', timeout=30000)
            self.current_url = self.page.url
            
            while time.time() < end_time and self.actions_taken < self.config.max_actions_per_session:
                try:
                    # Observe current state
                    state = await self._observe_page()
                    
                    # Check if stuck on same page
                    if self.page.url == self.current_url:
                        self.stuck_counter += 1
                    else:
                        self.stuck_counter = 0
                        self.current_url = self.page.url
                    
                    # If stuck on same page for 5+ actions, force navigation
                    if self.stuck_counter >= 5:
                        self.logger.warning(f"Stuck on {self.current_url} for {self.stuck_counter} actions")
                        next_action = await self._force_navigation(state)
                        self.stuck_counter = 0
                    else:
                        # Check if already explored
                        page_hash = self._hash_state(state)
                        if await self.shared_state.is_page_explored(page_hash):
                            # Try to find unexplored action
                            next_action = await self._get_unexplored_action(state)
                            if not next_action:
                                # LLM decides what to do
                                next_action = await self._decide_next_action(state)
                        else:
                            # Mark as explored and decide action
                            await self.shared_state.mark_page_explored(page_hash, state)
                            next_action = await self._decide_next_action(state)
                    
                    # Execute action
                    if next_action:
                        await self._execute_action(next_action)
                        self.actions_taken += 1
                        
                        # Small delay between actions
                        await asyncio.sleep(self.config.action_delay_ms / 1000)
                    else:
                        # No viable actions, try to backtrack or navigate somewhere new
                        await self._backtrack_or_explore_new()
                    
                except Exception as e:
                    self.logger.error(f"Error during exploration: {e}", exc_info=True)
                    # Record the error as a finding
                    await self._record_finding({
                        'type': 'agent_error',
                        'severity': 'medium',
                        'message': str(e),
                        'url': self.page.url,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Try to recover
                    await asyncio.sleep(2)
            
            self.logger.info(f"Exploration completed. Actions taken: {self.actions_taken}, Pages visited: {len(self.pages_visited)}")
            
        finally:
            await self.cleanup()
    
    async def _force_navigation(self, state: Dict) -> Dict:
        """Force navigation to a new page when stuck - NEW"""
        links = state.get('links', [])
        current_url = self.page.url
        
        # Find a link to a different page
        for link in links:
            url = link.get('url', '')
            if url and url != current_url and 'javascript:' not in url:
                self.logger.info(f"Forcing navigation to break stuck state: {url}")
                return {
                    'type': 'navigate',
                    'url': url,
                    'reasoning': 'Breaking stuck state'
                }
        
        # Try going back
        return {
            'type': 'back',
            'reasoning': 'Going back to escape stuck state'
        }
    
    async def _observe_page(self) -> Dict[str, Any]:
        """Capture current page state"""
        url = self.page.url
        self.pages_visited.add(url)
        
        # Analyze page using PageAnalyzer
        state = await self.page_analyzer.analyze(self.page)
        
        # Add URL and agent info
        state['url'] = url
        state['agent_id'] = self.agent_id
        state['timestamp'] = datetime.now().isoformat()
        
        return state
    
    async def _decide_next_action(self, state: Dict) -> Optional[Dict]:
        """Use LLM to decide next action"""
        # Get previously explored pages for context
        explored = await self.shared_state.get_explored_pages(limit=10)
        
        # Ask LLM for next action
        action = await self.llm.decide_action(
            current_state=state,
            explored_pages=explored,
            actions_taken=self.actions_taken
        )
        
        return action
    
    async def _get_unexplored_action(self, state: Dict) -> Optional[Dict]:
        """Find an action that hasn't been explored yet"""
        # Get links on this page
        links = state.get('links', [])
        
        # Prioritize links to new pages
        for link in links:
            url = link.get('url', '')
            if url and url not in self.pages_visited:
                if 'javascript:' not in url and not url.endswith('#'):
                    return {
                        'type': 'navigate',
                        'url': url,
                        'element_text': link.get('text', '')
                    }
        
        # Check interactive elements
        interactive_elements = state.get('interactive_elements', [])
        for element in interactive_elements:
            element_hash = self._hash_element(element)
            if not await self.shared_state.is_action_explored(element_hash):
                return {
                    'type': 'click',
                    'selector': element.get('selector'),
                    'element_text': element.get('text', '')
                }
        
        return None
    
    async def _execute_action(self, action: Dict):
        """Execute browser action - IMPROVED"""
        action_type = action.get('type')
        
        try:
            if action_type == 'click':
                selector = action.get('selector')
                self.logger.info(f"Clicking: {selector}")
                
                # Wait for element to be visible first
                await self.page.wait_for_selector(selector, state='visible', timeout=5000)
                await self.page.click(selector, timeout=5000)
                
                # Wait for navigation or network idle
                try:
                    await self.page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    await asyncio.sleep(1)  # Brief pause if no navigation
                
            elif action_type == 'fill':
                selector = action.get('selector')
                value = action.get('value', 'test')
                self.logger.info(f"Filling {selector} with: {value}")
                await self.page.fill(selector, value)
                
            elif action_type == 'navigate':
                url = action.get('url')
                if not url:
                    self.logger.error("Navigate action missing URL!")
                    return
                    
                self.logger.info(f"Navigating to: {url}")
                await self.page.goto(url, wait_until='networkidle', timeout=30000)
                
            elif action_type == 'scroll':
                self.logger.info("Scrolling page")
                await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(0.5)
            
            elif action_type == 'back':
                self.logger.info("Going back")
                await self.page.go_back(wait_until='networkidle', timeout=10000)
            
            # Take screenshot of result
            screenshot_path = self.config.screenshots_dir / f"agent{self.agent_id}_{self.actions_taken}.png"
            await self.page.screenshot(path=str(screenshot_path))
            
            # Mark action as explored
            action_hash = self._hash_action(action)
            await self.shared_state.mark_action_explored(action_hash, action)
            
        except Exception as e:
            self.logger.error(f"Failed to execute action {action_type}: {e}")
            await self._record_finding({
                'type': 'action_failure',
                'severity': 'low',
                'message': f"Failed to execute {action_type}: {str(e)}",
                'action': action,
                'url': self.page.url,
                'timestamp': datetime.now().isoformat()
            })
    
    async def _backtrack_or_explore_new(self):
        """Try to navigate to unexplored areas"""
        try:
            if len(self.pages_visited) > 1:
                await self.page.go_back(wait_until='networkidle', timeout=10000)
            else:
                await self.page.goto(self.config.base_url, wait_until='networkidle', timeout=30000)
        except:
            pass
    
    def _hash_state(self, state: Dict) -> str:
        """Create hash of page state for deduplication"""
        # Use URL path only (ignore query params)
        url = state['url'].split('?')[0]
        key = f"{url}_{state.get('title', '')}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _hash_element(self, element: Dict) -> str:
        """Create hash of element for tracking"""
        key = f"{element.get('selector')}_{element.get('text', '')}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _hash_action(self, action: Dict) -> str:
        """Create hash of action for tracking"""
        # Only hash the essential parts
        essential = {
            'type': action.get('type'),
            'selector': action.get('selector', ''),
            'url': action.get('url', '')
        }
        key = json.dumps(essential, sort_keys=True)
        return hashlib.md5(key.encode()).hexdigest()
    
    async def _record_finding(self, finding: Dict):
        """Record a bug or issue"""
        finding['agent_id'] = self.agent_id
        await self.shared_state.add_finding(finding)
        self.findings.append(finding)
        
        severity = finding.get('severity', 'unknown')
        self.logger.warning(f"Finding recorded: {severity} - {finding.get('message', 'No message')}")
    
    def _handle_js_error(self, error):
        """Handle JavaScript errors"""
        asyncio.create_task(self._record_finding({
            'type': 'javascript_error',
            'severity': 'high',
            'message': str(error),
            'url': self.page.url,
            'timestamp': datetime.now().isoformat()
        }))
    
    def _handle_console_message(self, msg):
        """Handle console messages"""
        if msg.type == 'error':
            asyncio.create_task(self._record_finding({
                'type': 'console_error',
                'severity': 'medium',
                'message': msg.text,
                'url': self.page.url,
                'timestamp': datetime.now().isoformat()
            }))
    
    def _handle_response(self, response):
        """Handle HTTP responses"""
        if response.status >= 400:
            asyncio.create_task(self._record_finding({
                'type': 'http_error',
                'severity': 'high' if response.status >= 500 else 'medium',
                'message': f"HTTP {response.status} - {response.url}",
                'url': self.page.url,
                'status_code': response.status,
                'timestamp': datetime.now().isoformat()
            }))
    
    async def cleanup(self):
        """Clean up browser resources"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        
        self.logger.info("Browser cleanup completed")
