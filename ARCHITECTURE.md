# Local Autonomous Web Testing System
## Architecture Overview

This system replicates Propolis's core functionality using local tools for internal network-restricted web apps.

### Components

```
┌─────────────────────────────────────────────────────────┐
│                   Swarm Orchestrator                     │
│  - Manages agent lifecycle                              │
│  - Coordinates exploration                              │
│  - Aggregates findings                                  │
└───────────────┬─────────────────────────────────────────┘
                │
                │ spawns & coordinates
                │
        ┌───────┴────────┬──────────────┬─────────────┐
        │                │              │             │
   ┌────▼─────┐    ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐
   │ Agent 1  │    │ Agent 2  │  │ Agent 3  │  │ Agent N  │
   │          │    │          │  │          │  │          │
   │ Playwright    │ Playwright    │ Playwright    │ Playwright
   │ Browser  │    │ Browser  │  │ Browser  │  │ Browser  │
   └────┬─────┘    └────┬─────┘  └────┬─────┘  └────┬─────┘
        │               │              │             │
        └───────┬───────┴──────────────┴─────────────┘
                │
                │ queries for decisions
                │
        ┌───────▼──────────────────┐
        │   Ollama (Local LLM)     │
        │   Llama 3.2:3B Model     │
        │                          │
        │  - Navigation decisions  │
        │  - Bug detection        │
        │  - Action planning      │
        └──────────────────────────┘
```

### Key Features

1. **Multi-Agent Swarm**: Run 5-20 concurrent agents (configurable based on system resources)
2. **Autonomous Exploration**: Agents discover and test flows without predefined scripts
3. **Shared Knowledge Base**: Agents communicate via Redis/SQLite to avoid duplicate work
4. **Intelligent Decision Making**: LLM-powered action selection and bug detection
5. **Comprehensive Reporting**: HTML reports with screenshots, traces, and reproduction steps

### Technology Stack

- **Ollama + Llama 3.2:3B**: Local LLM for agent reasoning (no internet needed)
- **Playwright**: Browser automation with Chrome, Firefox, or WebKit support
- **Python 3.10+**: Core orchestration language
- **SQLite/Redis**: Shared state between agents (SQLite for simplicity, Redis for performance)
- **asyncio**: Concurrent agent execution

### Agent Behavior

Each agent operates in cycles:

1. **Observe**: Capture current page state (DOM, screenshots, accessibility tree)
2. **Reason**: Query LLM to decide next action based on:
   - Current state
   - Explored paths (from shared DB)
   - Testing objectives
   - Previous actions
3. **Act**: Execute browser action (click, type, navigate)
4. **Evaluate**: Check for errors, bugs, or interesting findings
5. **Report**: Log findings to shared database
6. **Repeat**: Continue until time limit or coverage goal

### Data Flow

```
Agent observes page → Extracts simplified state → Sends to LLM → 
Receives action → Executes in browser → Checks for errors → 
Logs to shared DB → Next cycle
```

### Bug Detection Strategies

1. **Error Console Monitoring**: Capture JavaScript errors
2. **HTTP Failure Detection**: Track 4xx/5xx responses
3. **Visual Regression**: Screenshot comparison for major UI changes
4. **Accessibility Violations**: Check WCAG standards
5. **Performance Issues**: Track slow page loads (>5s)
6. **Broken Links**: Identify 404s and dead ends
7. **Form Validation**: Test edge cases (empty fields, SQL injection strings)

### Advantages Over Cloud Solutions

- **Network Isolation**: Runs entirely on internal network
- **No Data Leakage**: Testing data never leaves your infrastructure
- **Cost**: One-time setup, no per-test charges
- **Customization**: Full control over agent behavior
- **Privacy**: Sensitive credentials stay local
