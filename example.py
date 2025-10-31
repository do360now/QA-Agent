#!/usr/bin/env python3
"""
Quick start example - Demonstrates basic usage of the testing swarm
"""

import asyncio
from pathlib import Path
from config import Config
from swarm_orchestrator import SwarmOrchestrator


async def run_quick_test():
    """Run a quick 2-minute test with 2 agents"""
    
    print("🐝 Quick Test Example")
    print("=" * 60)
    print()
    
    # Configure the test
    config = Config(
        base_url="http://localhost:3000",  # Change to your app URL
        ollama_url="http://localhost:11434",
        model_name="llama3.2:3b",
        headless=False,  # Set to True for production use
        output_dir=Path("./test-results"),
        
        # Optional authentication
        # auth_username="testuser",
        # auth_password="testpass",
        
        # Test behavior
        max_actions_per_session=20,
        action_delay_ms=1000,  # 1 second between actions
        
        # Bug detection
        detect_js_errors=True,
        detect_http_errors=True,
        detect_slow_pages=True,
        slow_page_threshold_ms=5000
    )
    
    # Create orchestrator
    orchestrator = SwarmOrchestrator(config)
    
    try:
        print(f"Target: {config.base_url}")
        print(f"Agents: 2")
        print(f"Duration: 2 minutes")
        print()
        
        # Initialize
        await orchestrator.initialize()
        
        # Spawn 2 agents
        await orchestrator.spawn_agents(num_agents=2)
        
        # Run for 2 minutes
        await orchestrator.run_swarm(duration_minutes=2)
        
        # Generate report
        report_path = await orchestrator.generate_report()
        
        print()
        print("=" * 60)
        print("✅ Test Complete!")
        print()
        print(f"Report: {report_path}")
        print(f"Screenshots: {config.screenshots_dir}")
        print()
        print("Open the HTML report in your browser to see findings.")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        await orchestrator.cleanup()


async def run_custom_test():
    """Example with custom configuration"""
    
    config = Config(
        base_url="https://example.com",
        headless=True,
        
        # Custom authentication selectors
        auth_username="admin",
        auth_password="secret",
        auth_form_selectors={
            'username': ['#user-email', 'input[name="email"]'],
            'password': ['#user-password', 'input[type="password"]'],
            'submit': ['#login-button', 'button:has-text("Log in")']
        },
        
        # Aggressive exploration
        max_actions_per_session=100,
        action_delay_ms=500,
        
        # All bug detectors enabled
        detect_js_errors=True,
        detect_http_errors=True,
        detect_slow_pages=True,
        detect_broken_links=True,
        detect_accessibility=True
    )
    
    orchestrator = SwarmOrchestrator(config)
    
    try:
        await orchestrator.initialize()
        await orchestrator.spawn_agents(num_agents=5)
        await orchestrator.run_swarm(duration_minutes=10)
        await orchestrator.generate_report()
    finally:
        await orchestrator.cleanup()


if __name__ == '__main__':
    print()
    print("Choose example:")
    print("  1. Quick test (2 agents, 2 minutes, localhost:3000)")
    print("  2. Custom test (see code for configuration)")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(run_quick_test())
    elif choice == "2":
        asyncio.run(run_custom_test())
    else:
        print("Invalid choice. Running quick test...")
        asyncio.run(run_quick_test())
