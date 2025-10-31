"""
Configuration management for the testing swarm
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Configuration for the testing swarm"""
    
    # Target application
    base_url: str
    
    # Ollama settings
    ollama_url: str = "http://localhost:11434"
    model_name: str = "llama3.2:3b"
    
    # Browser settings
    headless: bool = False
    browser_type: str = "chromium"  # chromium, firefox, or webkit
    viewport_width: int = 1920
    viewport_height: int = 1080
    
    # Authentication
    auth_username: Optional[str] = None
    auth_password: Optional[str] = None
    auth_form_selectors: dict = None  # Custom selectors for login form
    
    # Output settings
    output_dir: Path = Path("./test-results")
    screenshots_dir: Optional[Path] = None
    traces_dir: Optional[Path] = None
    
    # Database
    db_path: Path = Path("./test-results/shared_state.db")
    
    # Agent behavior
    max_actions_per_session: int = 50
    action_delay_ms: int = 500  # Delay between actions
    page_load_timeout_ms: int = 30000
    
    # Exploration strategy
    exploration_strategy: str = "adaptive"  # adaptive, breadth-first, depth-first
    coverage_goal: float = 0.80  # Target 80% page coverage
    
    # Bug detection thresholds
    detect_js_errors: bool = True
    detect_http_errors: bool = True
    detect_slow_pages: bool = True
    slow_page_threshold_ms: int = 5000
    detect_broken_links: bool = True
    detect_accessibility: bool = True
    
    def __post_init__(self):
        """Initialize derived paths"""
        if self.screenshots_dir is None:
            self.screenshots_dir = self.output_dir / "screenshots"
        if self.traces_dir is None:
            self.traces_dir = self.output_dir / "traces"
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.traces_dir.mkdir(parents=True, exist_ok=True)
        
        # Set default auth form selectors if not provided
        if self.auth_form_selectors is None:
            self.auth_form_selectors = {
                'username': ['input[name="username"]', 'input[type="email"]', '#username', '#email'],
                'password': ['input[name="password"]', 'input[type="password"]', '#password'],
                'submit': ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("Login")', 'button:has-text("Sign in")']
            }
