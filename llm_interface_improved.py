"""
IMPROVED LLM Interface - Handles communication with Ollama with better exploration
"""

import json
import logging
from typing import Dict, List, Optional, Any
import aiohttp
from collections import Counter

from config import Config

logger = logging.getLogger(__name__)


class LLMInterface:
    """Interface to Ollama LLM for agent reasoning - IMPROVED VERSION"""
    
    def __init__(self, config: Config):
        self.config = config
        self.api_url = f"{config.ollama_url}/api/generate"
        self.model = config.model_name
        self.recent_actions = []  # Track recent actions to avoid loops
        
    async def decide_action(
        self,
        current_state: Dict,
        explored_pages: List[Dict],
        actions_taken: int
    ) -> Optional[Dict]:
        """Decide next action based on current page state"""
        
        # Check for action loops
        if self._is_stuck_in_loop():
            logger.warning("Agent appears stuck in loop, forcing different action")
            return self._get_different_action(current_state)
        
        # Build context-aware prompt
        prompt = self._build_action_prompt(current_state, explored_pages, actions_taken)
        
        # Query LLM
        response = await self._query_ollama(prompt)
        
        # Parse response into action
        action = self._parse_action_response(response, current_state)
        
        # Track this action
        if action:
            self._track_action(action)
        
        return action
    
    def _is_stuck_in_loop(self) -> bool:
        """Detect if agent is repeating same actions"""
        if len(self.recent_actions) < 5:
            return False
        
        # Check last 5 actions
        last_5 = self.recent_actions[-5:]
        action_strings = [json.dumps(a, sort_keys=True) for a in last_5]
        
        # If more than 3 of last 5 are identical, we're in a loop
        counter = Counter(action_strings)
        most_common_count = counter.most_common(1)[0][1] if counter else 0
        
        return most_common_count >= 3
    
    def _track_action(self, action: Dict):
        """Track action for loop detection"""
        # Only track selector and type, not reasoning
        tracked = {
            'type': action.get('type'),
            'selector': action.get('selector', '')[:50],  # Truncate long selectors
        }
        self.recent_actions.append(tracked)
        
        # Keep only last 10 actions
        if len(self.recent_actions) > 10:
            self.recent_actions.pop(0)
    
    def _get_different_action(self, state: Dict) -> Optional[Dict]:
        """Force a different action when stuck in loop"""
        
        # Get recent selectors to avoid
        recent_selectors = {a.get('selector') for a in self.recent_actions[-5:]}
        
        # Try to find an unexplored element
        interactive = state.get('interactive_elements', [])
        for element in interactive:
            selector = element.get('selector')
            if selector not in recent_selectors:
                logger.info(f"Breaking loop by trying different element: {selector}")
                return {
                    'type': 'click',
                    'selector': selector,
                    'reasoning': 'Breaking out of action loop'
                }
        
        # Try navigating to an unexplored link
        links = state.get('links', [])
        for link in links:
            url = link.get('url', '')
            if url and 'javascript:' not in url and '#' not in url:
                logger.info(f"Breaking loop by navigating to: {url}")
                return {
                    'type': 'navigate',
                    'url': url,
                    'reasoning': 'Breaking out of action loop'
                }
        
        # Last resort: scroll
        return {
            'type': 'scroll',
            'reasoning': 'Breaking out of action loop by scrolling'
        }
    
    async def analyze_for_bugs(self, state: Dict) -> List[Dict]:
        """Analyze page state for potential bugs"""
        
        prompt = self._build_bug_analysis_prompt(state)
        response = await self._query_ollama(prompt)
        
        # Parse bug findings
        bugs = self._parse_bug_response(response)
        
        return bugs
    
    def _build_action_prompt(
        self,
        state: Dict,
        explored_pages: List[Dict],
        actions_taken: int
    ) -> str:
        """Build prompt for action decision - IMPROVED"""
        
        # Simplify state for LLM
        interactive = state.get('interactive_elements', [])[:15]  # More elements
        links = state.get('links', [])[:10]  # More links
        forms = state.get('forms', [])
        
        # Get recently explored URLs to mention
        explored_urls = [p.get('url', '') for p in explored_pages[-5:]]
        
        prompt = f"""You are an autonomous web testing agent exploring a web application to find bugs and test functionality.

Current Page:
URL: {state.get('url', 'unknown')}
Title: {state.get('title', 'unknown')}

Recently Explored Pages:
{chr(10).join(f"- {url}" for url in explored_urls) if explored_urls else "None yet"}

Available Interactive Elements:
{self._format_elements(interactive)}

Available Links to Explore:
{self._format_links(links)}

Forms on Page: {len(forms)}

Actions taken: {actions_taken}/50

IMPORTANT RULES:
1. PRIORITIZE UNEXPLORED LINKS - Click links to new pages, not the current page
2. AVOID repetitive actions - Don't click the same link multiple times
3. Explore navigation menus (look for /agents, /dashboard, /login, etc.)
4. Test forms with various inputs
5. If on homepage, navigate to other sections
6. Look for buttons that trigger actions, not just navigation

Choose the BEST action to discover new functionality and potential bugs.

Respond with ONLY valid JSON (no markdown, no extra text):
{{
    "type": "click|fill|navigate|scroll",
    "selector": "CSS selector for click/fill",
    "url": "full URL for navigate",
    "value": "text value for fill action",
    "reasoning": "why this action explores new functionality"
}}

For navigate actions, ALWAYS include the full URL field.
If no good actions available, respond: {{"type": "none"}}

Your JSON response:"""
        
        return prompt
    
    def _build_bug_analysis_prompt(self, state: Dict) -> str:
        """Build prompt for bug detection"""
        
        errors = state.get('errors', [])
        
        prompt = f"""You are a QA expert analyzing a web page for potential bugs.

Page Information:
URL: {state.get('url')}
Title: {state.get('title')}
Load Time: {state.get('load_time_ms', 0)}ms

Errors Detected:
{json.dumps(errors, indent=2)}

Forms: {len(state.get('forms', []))}
Images: {len(state.get('images', []))}
Interactive Elements: {len(state.get('interactive_elements', []))}

Analyze this page for bugs and issues. Consider:
- JavaScript errors
- Slow page load times (>5000ms is concerning)
- Missing or broken images
- Empty required form fields
- Accessibility issues
- HTTP errors

Respond with a JSON array of bugs found (empty array if none):
[
    {{
        "type": "bug_type",
        "severity": "low|medium|high|critical",
        "message": "description of the bug"
    }}
]

Your response (JSON only):"""
        
        return prompt
    
    async def _query_ollama(self, prompt: str, max_retries: int = 3) -> str:
        """Query Ollama API"""
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,  # Slightly higher for more variety
                "num_predict": 500   # Limit response length
            }
        }
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.api_url, json=payload, timeout=30) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data.get('response', '').strip()
                        else:
                            logger.error(f"Ollama API error: {response.status}")
                            
            except Exception as e:
                logger.error(f"Failed to query Ollama (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return ""
    
    def _parse_action_response(self, response: str, state: Dict) -> Optional[Dict]:
        """Parse LLM response into action dictionary - IMPROVED"""
        
        try:
            # Try to extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                action = json.loads(json_str)
                
                # Validate action
                if action.get('type') == 'none':
                    return None
                
                if 'type' not in action:
                    logger.warning("LLM response missing 'type' field")
                    return self._fallback_action(state)
                
                # Validate navigate actions have URL
                if action['type'] == 'navigate':
                    if not action.get('url'):
                        logger.warning("Navigate action missing URL")
                        return self._fallback_action(state)
                
                # Validate click/fill actions have selector
                if action['type'] in ['click', 'fill']:
                    if not action.get('selector'):
                        logger.warning(f"{action['type']} action missing selector")
                        return self._fallback_action(state)
                
                return action
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Response was: {response}")
        
        # Fallback
        return self._fallback_action(state)
    
    def _parse_bug_response(self, response: str) -> List[Dict]:
        """Parse bug analysis response"""
        
        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                bugs = json.loads(json_str)
                return bugs if isinstance(bugs, list) else []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse bug response: {e}")
        
        return []
    
    def _fallback_action(self, state: Dict) -> Optional[Dict]:
        """Generate fallback action when LLM fails - IMPROVED"""
        
        # Get recent selectors to avoid
        recent_selectors = {a.get('selector') for a in self.recent_actions[-3:]}
        
        # Try to find an unexplored link first (better for navigation)
        links = state.get('links', [])
        for link in links:
            url = link.get('url', '')
            current_url = state.get('url', '')
            
            # Skip javascript, anchors, and current page
            if url and url != current_url:
                if 'javascript:' not in url and not url.endswith('#'):
                    logger.info(f"Fallback: navigating to {url}")
                    return {
                        'type': 'navigate',
                        'url': url,
                        'reasoning': 'Fallback: exploring new page'
                    }
        
        # Try to click interactive element that we haven't clicked recently
        interactive = state.get('interactive_elements', [])
        for element in interactive:
            selector = element.get('selector')
            if selector not in recent_selectors:
                logger.info(f"Fallback: clicking {selector}")
                return {
                    'type': 'click',
                    'selector': selector,
                    'reasoning': 'Fallback: clicking unexplored element'
                }
        
        # Last resort: scroll
        return {
            'type': 'scroll',
            'reasoning': 'Fallback: scrolling to reveal more content'
        }
    
    def _format_elements(self, elements: List[Dict]) -> str:
        """Format interactive elements for prompt - IMPROVED"""
        if not elements:
            return "None found"
        
        lines = []
        for i, elem in enumerate(elements, 1):
            text = elem.get('text', '')[:60]  # More text
            selector = elem.get('selector', 'unknown')
            elem_type = elem.get('type', 'unknown')
            
            # Make it clearer what the element does
            lines.append(f"{i}. [{elem_type}] {selector} - \"{text}\"")
        
        return "\n".join(lines)
    
    def _format_links(self, links: List[Dict]) -> str:
        """Format links for prompt - IMPROVED"""
        if not links:
            return "None found"
        
        lines = []
        for i, link in enumerate(links, 1):
            url = link.get('url', '')
            text = link.get('text', '')[:60]
            
            # Highlight if it's a new section
            if '/agents' in url or '/dashboard' in url or '/login' in url:
                lines.append(f"{i}. ⭐ {url} - \"{text}\" (NEW SECTION)")
            else:
                lines.append(f"{i}. {url} - \"{text}\"")
        
        return "\n".join(lines)


# Allow asyncio in synchronous context
import asyncio
