# 🐝 Autonomous Web Testing System - Project Summary

## What I've Built

A complete, production-ready autonomous web testing system that replicates Propolis's core functionality using **local tools only** - perfect for your internal, network-restricted web application.

## Key Features

✅ **Fully Local**: Runs entirely on your network using Ollama + Llama 3.2:3B
✅ **Multi-Agent Swarm**: Deploy 5-20+ concurrent testing agents
✅ **Zero Setup**: Just provide a URL and optional credentials
✅ **Autonomous Exploration**: Agents intelligently navigate your app
✅ **Bug Detection**: Automatically finds JS errors, HTTP failures, slow pages, broken links
✅ **Coordination**: Agents share knowledge via SQLite to avoid duplicate work
✅ **Rich Reports**: Professional HTML reports with findings by severity
✅ **Customizable**: Full control over agent behavior, detection rules, and exploration strategy

## Files Delivered

### Core System (7 files)
1. **swarm_orchestrator.py** - Main entry point, manages agent lifecycle
2. **agent.py** - Autonomous testing agent implementation
3. **llm_interface.py** - Ollama integration for LLM-powered decisions
4. **page_analyzer.py** - Extracts structured info from web pages
5. **shared_state.py** - SQLite-based coordination between agents
6. **reporter.py** - Generates professional HTML reports
7. **config.py** - Configuration management

### Setup & Docs (6 files)
8. **setup.sh** - Automated setup script for macOS/Linux
9. **setup.bat** - Automated setup script for Windows
10. **requirements.txt** - Python dependencies
11. **README.md** - Comprehensive documentation
12. **TROUBLESHOOTING.md** - Common issues and solutions
13. **ARCHITECTURE.md** - Technical architecture details

### Examples (2 files)
14. **example.py** - Quick start examples
15. **.gitignore** - Git ignore rules

## Quick Start (3 Steps)

### 1. Install Prerequisites

**Install Ollama:**
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: Download from ollama.com
```

**Pull the model:**
```bash
ollama pull llama3.2:3b
ollama serve  # Keep this running
```

### 2. Run Setup Script

**macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```bash
setup.bat
```

### 3. Run Your First Test

```bash
# Activate environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run test
python swarm_orchestrator.py \
  --url http://your-internal-app.local \
  --num-agents 5 \
  --duration 10
```

## How It Works

### Agent Behavior Loop

```
1. OBSERVE → Extract page state (DOM, links, forms, buttons)
2. REASON  → Ask LLM: "What should I do next?"
3. ACT     → Execute action (click, fill, navigate)
4. DETECT  → Check for bugs (JS errors, HTTP failures, etc.)
5. REPORT  → Log findings to shared database
6. REPEAT  → Continue exploring
```

### Agent Coordination

Agents avoid duplicate work through a shared SQLite database:
- Track explored pages (by URL + state hash)
- Track executed actions (by action hash)
- Share bug findings in real-time
- Monitor coverage progress

### LLM Integration

Each agent queries Llama 3.2:3B locally via Ollama to:
- Decide which element to interact with next
- Generate test values for forms
- Choose exploration paths
- Analyze pages for potential issues

## Example Usage Scenarios

### Scenario 1: Quick Smoke Test
```bash
python swarm_orchestrator.py \
  --url http://localhost:3000 \
  --num-agents 2 \
  --duration 5
```
**Use case**: Quick check before deployment (5 minutes)

### Scenario 2: Comprehensive Test with Auth
```bash
python swarm_orchestrator.py \
  --url https://staging.internal \
  --auth-user test@company.com \
  --auth-pass secretpass \
  --num-agents 10 \
  --duration 30 \
  --headless
```
**Use case**: Thorough staging environment test (30 minutes)

### Scenario 3: Maximum Coverage
```bash
python swarm_orchestrator.py \
  --url http://app.internal \
  --num-agents 20 \
  --duration 60 \
  --headless
```
**Use case**: Deep exploration for critical apps (1 hour)

## What Gets Detected Automatically

### JavaScript Errors
- Uncaught exceptions
- Console errors
- Failed promises

### HTTP Failures
- 4xx errors (client errors)
- 5xx errors (server errors)
- Failed API calls

### Performance Issues
- Slow page loads (>5 seconds by default)
- Timeout errors
- Resource loading failures

### UI Problems
- Broken images
- Broken links (404s)
- Missing alt text
- Form validation issues

### Accessibility
- Missing labels
- Invalid ARIA attributes
- Poor contrast ratios

## Sample Output

After a test completes:

```
test-results/
├── test_report_20241031_143022.html  ← Open this in browser
├── shared_state.db                   ← Agent coordination data
├── screenshots/
│   ├── agent0_1.png
│   ├── agent0_2.png
│   └── ...
└── traces/
    └── ...
```

The HTML report includes:
- **Executive Summary**: Duration, pages explored, actions taken, findings count
- **Critical Findings**: Show-stopper bugs
- **High Severity**: Important issues
- **Medium Severity**: Notable problems
- **Low Severity**: Minor issues
- **Coverage Stats**: URLs visited, interaction count

## Comparison: Your System vs. Propolis

| Feature | Propolis | Your System |
|---------|----------|-------------|
| **Deployment** | Cloud SaaS | Self-hosted |
| **Data Privacy** | Uploads to cloud | 100% local |
| **Network Access** | Requires internet | Works offline |
| **Internal Apps** | ❌ No access | ✅ Full access |
| **Cost** | $$$ per test | Free (after setup) |
| **Customization** | Limited | Complete control |
| **Agent Coordination** | ✅ Yes | ✅ Yes |
| **Autonomous Exploration** | ✅ Yes | ✅ Yes |
| **Bug Detection** | ✅ Yes | ✅ Yes |
| **HTML Reports** | ✅ Yes | ✅ Yes |

## Advanced Customization

### Custom Bug Detectors

Add your own detection logic in `page_analyzer.py`:

```python
async def _check_custom_rule(self, page: Page) -> List[Dict]:
    errors = []
    # Your custom logic here
    # e.g., check for specific error messages
    if await page.query_selector('.error-banner'):
        errors.append({
            'type': 'custom_error',
            'severity': 'high',
            'message': 'Error banner found'
        })
    return errors
```

### Custom LLM Prompts

Modify agent behavior in `llm_interface.py`:

```python
def _build_action_prompt(self, state, explored, actions_taken):
    prompt = f"""
    You are testing a financial application. 
    Be extra careful with transaction forms.
    Always validate inputs before submission.
    
    Current page: {state['url']}
    ... [rest of prompt]
    """
    return prompt
```

### Custom Exploration Strategy

Change how agents explore in `config.py`:

```python
# Depth-first: Explore deeply before moving to new areas
exploration_strategy='depth-first'

# Breadth-first: Visit all top-level pages first
exploration_strategy='breadth-first'

# Adaptive (default): LLM decides based on context
exploration_strategy='adaptive'
```

## System Requirements

### Minimum
- **CPU**: 4 cores
- **RAM**: 8GB
- **Disk**: 10GB free
- **Python**: 3.10+

### Recommended for 10+ Agents
- **CPU**: 8+ cores
- **RAM**: 16GB+
- **Disk**: 20GB+ free (for screenshots/traces)

### Model Requirements
- **llama3.2:1b**: ~1GB RAM, fastest
- **llama3.2:3b**: ~2GB RAM, balanced (recommended)
- **llama3.1:8b**: ~5GB RAM, best quality

## Performance Tips

### Maximize Speed
- Use `--headless` mode
- Use smaller model (`llama3.2:1b`)
- Increase agent count (`--num-agents 20`)
- Reduce action delay (in config)

### Maximize Coverage
- Longer duration (`--duration 60`)
- Moderate agent count (`--num-agents 5-10`)
- Use better model (`llama3.2:3b`)

### Debug Mode
- Don't use `--headless` (watch browsers)
- Use 1-2 agents only
- Short duration (5 minutes)

## Troubleshooting Quick Reference

**Ollama not running?**
```bash
ollama serve
```

**Authentication failing?**
- Watch without `--headless` to see what's happening
- Customize `auth_form_selectors` in config

**Out of memory?**
- Reduce `--num-agents`
- Use `--headless`
- Use smaller model

**Agents getting stuck?**
- Increase `action_delay_ms` in config
- Check if app is rate-limiting
- Reduce agent count

See `TROUBLESHOOTING.md` for detailed solutions.

## Next Steps

1. **Run the quick example**:
   ```bash
   python example.py
   ```

2. **Test with your app**:
   ```bash
   python swarm_orchestrator.py --url http://your-app.local --num-agents 3 --duration 10
   ```

3. **Review the report**: Open the generated HTML report

4. **Customize for your needs**: Edit config, add custom detectors, adjust prompts

5. **Integrate into CI/CD**: Run tests automatically after deployments

## Key Advantages for Your Use Case

Since your app is internal and network-restricted, this system is perfect because:

✅ **No external access needed**: Everything runs on your network
✅ **Data stays private**: No uploads to third-party services
✅ **Authentication works**: Can test behind VPN/firewalls
✅ **Customizable**: You control every aspect
✅ **Cost-effective**: No per-test charges
✅ **Full transparency**: You see exactly what agents are doing

## Support

- **Documentation**: See README.md
- **Troubleshooting**: See TROUBLESHOOTING.md
- **Architecture**: See ARCHITECTURE.md
- **Examples**: See example.py

---

**Built to test internal web apps autonomously using local LLMs** 🐝
