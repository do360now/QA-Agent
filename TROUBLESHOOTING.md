# Troubleshooting Guide

## Common Issues and Solutions

### 1. Ollama Connection Errors

**Error**: `Failed to query Ollama` or `Connection refused on localhost:11434`

**Solutions**:
```bash
# Check if Ollama is running
curl http://localhost:11434

# If not running, start it
ollama serve

# Verify the model is available
ollama list
```

### 2. Browser Launch Failures

**Error**: `Browser was not found` or `Playwright not installed`

**Solutions**:
```bash
# Reinstall Playwright browsers
playwright install chromium

# Or install all browsers
playwright install

# On Linux, you may need dependencies
sudo playwright install-deps
```

### 3. Authentication Failures

**Problem**: Agents can't log in to your app

**Solutions**:

1. **Watch what's happening**: Run without `--headless` to see the browser
   ```bash
   python swarm_orchestrator.py --url http://your-app.local --auth-user test --auth-pass test123
   ```

2. **Customize selectors**: Edit `config.py` to match your login form
   ```python
   auth_form_selectors={
       'username': ['#your-username-field', 'input[name="email"]'],
       'password': ['#your-password-field'],
       'submit': ['#login-btn']
   }
   ```

3. **Test login manually**: Verify credentials work in a normal browser first

### 4. Agents Getting Stuck

**Problem**: Agents stop making progress or visit same pages repeatedly

**Solutions**:

1. **Reduce agent count**: Start with 2-3 agents
   ```bash
   python swarm_orchestrator.py --url http://your-app.local --num-agents 2
   ```

2. **Increase action delay**: Give the app more time
   ```python
   # In config.py
   action_delay_ms=2000  # 2 seconds between actions
   ```

3. **Check app logs**: Your app might be rate-limiting or blocking requests

### 5. Out of Memory Errors

**Problem**: System runs out of RAM

**Solutions**:

1. **Reduce agents**: Fewer concurrent browsers
   ```bash
   --num-agents 3  # Instead of 10
   ```

2. **Use headless mode**: Saves ~50% memory
   ```bash
   --headless
   ```

3. **Use smaller model**: Switch to lighter model
   ```bash
   --model llama3.2:1b
   ```

### 6. Slow Performance

**Problem**: Test runs very slowly

**Causes and solutions**:

1. **Large model**: Switch to faster model
   ```bash
   ollama pull llama3.2:1b
   python swarm_orchestrator.py --model llama3.2:1b
   ```

2. **Too many agents**: Reduce concurrent agents
   ```bash
   --num-agents 3
   ```

3. **Slow network**: Increase timeouts
   ```python
   # In config.py
   page_load_timeout_ms=60000  # 60 seconds
   ```

### 7. No Findings Reported

**Problem**: Test completes but reports zero bugs

**Possible reasons**:

1. **App is actually working well** ✅ (good news!)

2. **Agents aren't exploring enough**: Increase duration
   ```bash
   --duration 30  # 30 minutes instead of 10
   ```

3. **Bug detection disabled**: Check config
   ```python
   detect_js_errors=True
   detect_http_errors=True
   detect_slow_pages=True
   ```

4. **Agents getting authentication wrong**: Fix auth first

### 8. LLM Returns Invalid JSON

**Error**: `Failed to parse LLM response`

**Solutions**:

1. **Model too small**: Try larger model
   ```bash
   ollama pull llama3.2:3b  # Or llama3.1:8b
   ```

2. **Check Ollama logs**: Look for errors
   ```bash
   ollama serve  # Watch the output
   ```

3. **Fallback works**: System will use fallback actions automatically

### 9. Permission Errors

**Error**: `Permission denied` when creating files

**Solutions**:

```bash
# Check output directory permissions
ls -la test-results/

# Create with correct permissions
mkdir -p test-results
chmod 755 test-results

# Or specify different location
python swarm_orchestrator.py --output-dir ~/my-tests
```

### 10. Port Already in Use

**Error**: `Address already in use: 4723`

**Solution**:
```bash
# Kill existing process
lsof -ti:4723 | xargs kill -9

# Or use different port
# (This is for Appium, not needed for web testing)
```

## Debug Mode

Enable detailed logging:

```python
# In swarm_orchestrator.py, change logging level
logging.basicConfig(
    level=logging.DEBUG,  # Instead of INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Performance Optimization

### For Maximum Speed

```bash
python swarm_orchestrator.py \
  --url http://your-app.local \
  --num-agents 15 \
  --headless \
  --model llama3.2:1b \
  --duration 20
```

### For Maximum Coverage

```bash
python swarm_orchestrator.py \
  --url http://your-app.local \
  --num-agents 5 \
  --model llama3.2:3b \
  --duration 60
```

### For Debugging

```bash
python swarm_orchestrator.py \
  --url http://your-app.local \
  --num-agents 1 \
  --duration 5
  # No --headless flag (watch browser)
```

## Checking System Requirements

### Memory Check
```bash
# Linux/macOS
free -h

# Estimate needed: ~200MB per agent + ~500MB for model
# For 10 agents: ~2.5GB RAM recommended
```

### CPU Check
```bash
# See CPU usage
top  # or htop

# Each agent uses ~5-10% CPU
# Model inference: ~20-30% CPU per query
```

### Disk Space
```bash
# Check available space
df -h

# Screenshots can use ~10MB per agent per test
# Database: ~10-50MB
# Traces (if enabled): ~100MB+
```

## Getting Help

### Check Logs

1. **Swarm orchestrator logs**: Shows agent activity
2. **Ollama logs**: Run `ollama serve` to see LLM queries
3. **Shared database**: Check `test-results/shared_state.db`
   ```bash
   sqlite3 test-results/shared_state.db "SELECT * FROM findings;"
   ```

### Verify Setup

```bash
# Python version
python --version  # Should be 3.10+

# Ollama status
ollama list

# Playwright
playwright --version

# Dependencies
pip list | grep -E 'playwright|aiohttp|aiosqlite'
```

## Still Having Issues?

1. **Review error messages carefully**
2. **Check all prerequisites are installed**
3. **Try the example script**: `python example.py`
4. **Reduce complexity**: Start with 1-2 agents, short duration
5. **Test with a simple public website first** (e.g., example.com)
