"""
Page Analyzer - Extracts structured information from web pages
"""

import logging
from typing import Dict, List, Any
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class PageAnalyzer:
    """Analyzes web pages and extracts structured information"""
    
    def __init__(self, config):
        self.config = config
    
    async def analyze(self, page: Page) -> Dict[str, Any]:
        """Extract comprehensive page information"""
        
        state = {
            'url': page.url,
            'title': await page.title(),
            'interactive_elements': await self._extract_interactive_elements(page),
            'links': await self._extract_links(page),
            'forms': await self._extract_forms(page),
            'images': await self._extract_images(page),
            'errors': [],
            'load_time_ms': 0
        }
        
        # Check for various issues
        if self.config.detect_js_errors:
            state['errors'].extend(await self._check_js_errors(page))
        
        if self.config.detect_broken_links:
            state['errors'].extend(await self._check_broken_images(page))
        
        return state
    
    async def _extract_interactive_elements(self, page: Page) -> List[Dict]:
        """Extract clickable/interactive elements"""
        
        try:
            elements = await page.evaluate("""
                () => {
                    const interactive = [];
                    const selectors = [
                        'button',
                        'a[href]',
                        'input[type="submit"]',
                        '[role="button"]',
                        '[onclick]',
                        'select',
                        'textarea'
                    ];
                    
                    selectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach((el, idx) => {
                            // Generate unique selector
                            const tag = el.tagName.toLowerCase();
                            const id = el.id ? `#${el.id}` : '';
                            const classes = el.className ? `.${el.className.split(' ').join('.')}` : '';
                            
                            interactive.push({
                                selector: id || `${tag}${classes}:nth-of-type(${idx + 1})`,
                                tag: tag,
                                text: el.textContent?.trim().substring(0, 100) || '',
                                type: el.type || selector,
                                visible: el.offsetParent !== null
                            });
                        });
                    });
                    
                    // Filter to visible elements only
                    return interactive.filter(el => el.visible).slice(0, 50);
                }
            """)
            
            return elements or []
            
        except Exception as e:
            logger.error(f"Failed to extract interactive elements: {e}")
            return []
    
    async def _extract_links(self, page: Page) -> List[Dict]:
        """Extract all links from page"""
        
        try:
            links = await page.evaluate("""
                () => {
                    const links = [];
                    document.querySelectorAll('a[href]').forEach(a => {
                        links.push({
                            url: a.href,
                            text: a.textContent?.trim().substring(0, 100) || '',
                            target: a.target || '_self'
                        });
                    });
                    return links.slice(0, 100);
                }
            """)
            
            return links or []
            
        except Exception as e:
            logger.error(f"Failed to extract links: {e}")
            return []
    
    async def _extract_forms(self, page: Page) -> List[Dict]:
        """Extract form information"""
        
        try:
            forms = await page.evaluate("""
                () => {
                    const forms = [];
                    document.querySelectorAll('form').forEach((form, idx) => {
                        const inputs = [];
                        form.querySelectorAll('input, textarea, select').forEach(input => {
                            inputs.push({
                                name: input.name || input.id || '',
                                type: input.type || 'text',
                                required: input.required,
                                placeholder: input.placeholder || ''
                            });
                        });
                        
                        forms.push({
                            id: form.id || `form-${idx}`,
                            action: form.action,
                            method: form.method || 'GET',
                            inputs: inputs
                        });
                    });
                    
                    return forms;
                }
            """)
            
            return forms or []
            
        except Exception as e:
            logger.error(f"Failed to extract forms: {e}")
            return []
    
    async def _extract_images(self, page: Page) -> List[Dict]:
        """Extract image information"""
        
        try:
            images = await page.evaluate("""
                () => {
                    const images = [];
                    document.querySelectorAll('img').forEach(img => {
                        images.push({
                            src: img.src,
                            alt: img.alt || '',
                            loaded: img.complete && img.naturalHeight !== 0
                        });
                    });
                    return images;
                }
            """)
            
            return images or []
            
        except Exception as e:
            logger.error(f"Failed to extract images: {e}")
            return []
    
    async def _check_js_errors(self, page: Page) -> List[Dict]:
        """Check for JavaScript errors in console"""
        # This is handled by page.on('pageerror') in agent
        return []
    
    async def _check_broken_images(self, page: Page) -> List[Dict]:
        """Check for broken images"""
        
        errors = []
        
        try:
            images = await page.evaluate("""
                () => {
                    const broken = [];
                    document.querySelectorAll('img').forEach(img => {
                        if (!img.complete || img.naturalHeight === 0) {
                            broken.push({
                                src: img.src,
                                alt: img.alt || 'no alt text'
                            });
                        }
                    });
                    return broken;
                }
            """)
            
            for img in images:
                errors.append({
                    'type': 'broken_image',
                    'severity': 'medium',
                    'message': f"Broken image: {img['src']}"
                })
                
        except Exception as e:
            logger.error(f"Failed to check broken images: {e}")
        
        return errors
