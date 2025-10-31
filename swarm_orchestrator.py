#!/usr/bin/env python3
"""
Swarm Orchestrator - Main entry point for autonomous web testing
Manages multiple concurrent testing agents exploring a web application
"""

import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json

from config import Config
from agent import TestingAgent
from shared_state import SharedState
from reporter import HTMLReporter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SwarmOrchestrator:
    """Manages a swarm of autonomous testing agents"""
    
    def __init__(self, config: Config):
        self.config = config
        self.shared_state = SharedState(config.db_path)
        self.agents: List[TestingAgent] = []
        self.start_time = datetime.now()
        
    async def initialize(self):
        """Initialize shared resources"""
        await self.shared_state.initialize()
        logger.info(f"Initialized shared state database at {self.config.db_path}")
        
    async def spawn_agents(self, num_agents: int):
        """Create and start testing agents"""
        logger.info(f"Spawning {num_agents} testing agents...")
        
        for i in range(num_agents):
            agent = TestingAgent(
                agent_id=i,
                config=self.config,
                shared_state=self.shared_state
            )
            self.agents.append(agent)
        
        logger.info(f"Created {len(self.agents)} agents")
    
    async def run_swarm(self, duration_minutes: int):
        """Run all agents concurrently for specified duration"""
        logger.info(f"Starting swarm test for {duration_minutes} minutes")
        logger.info(f"Target URL: {self.config.base_url}")
        
        # Create tasks for all agents
        tasks = [
            agent.explore(duration_minutes=duration_minutes)
            for agent in self.agents
        ]
        
        # Run all agents concurrently
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except KeyboardInterrupt:
            logger.info("Swarm interrupted by user")
        
        logger.info("All agents completed exploration")
    
    async def generate_report(self):
        """Generate comprehensive test report"""
        findings = await self.shared_state.get_all_findings()
        coverage = await self.shared_state.get_coverage_stats()
        
        reporter = HTMLReporter(
            findings=findings,
            coverage=coverage,
            duration=(datetime.now() - self.start_time).total_seconds(),
            config=self.config
        )
        
        report_path = reporter.generate()
        logger.info(f"Report generated: {report_path}")
        return report_path
    
    async def cleanup(self):
        """Clean up resources"""
        for agent in self.agents:
            await agent.cleanup()
        await self.shared_state.close()
        logger.info("Cleanup completed")


async def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Web Testing Swarm using Ollama and Playwright"
    )
    parser.add_argument(
        '--url',
        required=True,
        help='Base URL of the web application to test'
    )
    parser.add_argument(
        '--num-agents',
        type=int,
        default=5,
        help='Number of concurrent agents (default: 5)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=30,
        help='Test duration in minutes (default: 30)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browsers in headless mode'
    )
    parser.add_argument(
        '--auth-user',
        help='Username for authentication'
    )
    parser.add_argument(
        '--auth-pass',
        help='Password for authentication'
    )
    parser.add_argument(
        '--output-dir',
        default='./test-results',
        help='Directory for test results (default: ./test-results)'
    )
    parser.add_argument(
        '--ollama-url',
        default='http://localhost:11434',
        help='Ollama API URL (default: http://localhost:11434)'
    )
    parser.add_argument(
        '--model',
        default='llama3.2:3b',
        help='Ollama model to use (default: llama3.2:3b)'
    )
    
    args = parser.parse_args()
    
    # Create configuration
    config = Config(
        base_url=args.url,
        ollama_url=args.ollama_url,
        model_name=args.model,
        headless=args.headless,
        output_dir=Path(args.output_dir),
        auth_username=args.auth_user,
        auth_password=args.auth_pass
    )
    
    # Create output directory
    config.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize orchestrator
    orchestrator = SwarmOrchestrator(config)
    
    try:
        await orchestrator.initialize()
        await orchestrator.spawn_agents(args.num_agents)
        await orchestrator.run_swarm(duration_minutes=args.duration)
        report_path = await orchestrator.generate_report()
        
        print(f"\n{'='*60}")
        print(f"Test Completed!")
        print(f"Duration: {args.duration} minutes")
        print(f"Agents: {args.num_agents}")
        print(f"Report: {report_path}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        logger.error(f"Swarm test failed: {e}", exc_info=True)
        raise
    finally:
        await orchestrator.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
