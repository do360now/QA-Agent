# 🚀 Quick Start Guide (5 Minutes)

This guide gets you from zero to running your first autonomous test in 5 minutes.

## Step 1: Install Ollama (2 minutes)

### macOS
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows
Download from: https://ollama.com/download

## Step 2: Get the Model (2 minutes)

```bash
# Pull the AI model (downloads ~2GB)
ollama pull llama3.2:3b

# Start Ollama server
ollama serve
```

Leave this terminal open and running!

## Step 3: Setup Python Environment (1 minute)

### macOS/Linux
```bash
./setup.sh
```

### Windows
```bash
setup.bat
```

This will:
- Create Python virtual environment
- Install dependencies (Playwright, aiohttp, etc.)
- Download browser binaries

## Step 4: Run Your First Test! 🎉

```bash
# Activate environment
source venv/bin/activate    # macOS/Linux
# OR
venv\Scripts\activate       # Windows

# Run test
python swarm_orchestrator.py \
  --url http://localhost:3000 \
  --num-agents 3 \
  --duration 5
```

**Replace `http://localhost:3000` with your app's URL!**

## What Happens Next?

You'll see agents starting up:
```
INFO - Spawning 3 testing agents...
INFO - Agent-0: Browser initialized
INFO - Agent-1: Browser initialized  
INFO - Agent-2: Browser initialized
INFO - Starting swarm test for 5 minutes
```

Agents will:
1. Open browsers (you can watch them!)
2. Navigate your app
3. Click buttons, fill forms
4. Detect bugs automatically
5. Generate a report

## View Results

After 5 minutes:
```
Test Completed!
Report: ./test-results/test_report_20241031_143022.html
```

**Open that HTML file in your browser!**

## Common First-Run Issues

### "Ollama not running"
```bash
# In a separate terminal:
ollama serve
```

### "Browser not found"
```bash
playwright install chromium
```

### "Authentication failing"
Add credentials:
```bash
python swarm_orchestrator.py \
  --url http://your-app.local \
  --auth-user yourusername \
  --auth-pass yourpassword \
  --num-agents 3 \
  --duration 5
```

## Next Steps

### 1. Run Longer Test
```bash
python swarm_orchestrator.py \
  --url http://your-app.local \
  --num-agents 10 \
  --duration 30 \
  --headless
```

### 2. Review Documentation
- **README.md** - Full documentation
- **TROUBLESHOOTING.md** - Solutions to common issues
- **example.py** - Code examples

### 3. Customize for Your App
Edit `config.py` to:
- Change exploration strategy
- Add custom bug detectors
- Adjust timing and thresholds
- Configure authentication selectors

## Visual Guide: How It Works

```
┌─────────────────────────────────────────┐
│         YOU                             │
│  Run: python swarm_orchestrator.py     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│    SWARM ORCHESTRATOR                    │
│  • Manages agent lifecycle               │
│  • Coordinates exploration               │
│  • Generates reports                     │
└──────┬─────────────────┬─────────────────┘
       │                 │
       ▼                 ▼
   ┌───────┐        ┌───────┐
   │Agent 1│        │Agent 2│ ... (more agents)
   └───┬───┘        └───┬───┘
       │                │
       ▼                ▼
   ┌─────────────────────────────┐
   │  OLLAMA + Llama 3.2:3B      │
   │  (Running on your machine)  │
   │  • Decides what to click    │
   │  • Analyzes for bugs        │
   │  • Plans exploration        │
   └─────────────────────────────┘
       ▲                │
       │                ▼
   ┌───────────────────────────────┐
   │  YOUR WEB APP                 │
   │  (Internal, network-restricted)│
   │  • Gets tested automatically  │
   │  • Errors/bugs are found      │
   └───────────────────────────────┘
               │
               ▼
   ┌───────────────────────────────┐
   │  HTML REPORT                  │
   │  • All bugs found             │
   │  • Screenshots                │
   │  • Coverage stats             │
   └───────────────────────────────┘
```

## Pro Tips

### Tip 1: Start Small
Begin with 2 agents for 5 minutes to verify everything works.

### Tip 2: Watch First Run
Don't use `--headless` on your first test - watch the browsers to see what's happening!

### Tip 3: Check Auth Early
If your app needs login, test authentication first with 1 agent before scaling up.

### Tip 4: Use Headless for Production
Once comfortable, always use `--headless` for better performance.

### Tip 5: Read the Reports
The HTML reports are comprehensive - spend time reviewing findings.

## Example Timeline

**Minute 0-2**: Install Ollama, pull model
**Minute 2-3**: Run setup script  
**Minute 3**: Launch first test
**Minute 3-8**: Agents explore (5 minute test)
**Minute 8**: Review HTML report

Total: **8 minutes from zero to results!**

## Help!

If stuck:
1. Check `TROUBLESHOOTING.md`
2. Run with 1 agent first: `--num-agents 1`
3. Check Ollama is running: `curl http://localhost:11434`
4. Verify Python version: `python --version` (need 3.10+)

## Success Criteria

You know it's working when:
✅ Agents open browsers
✅ Browsers navigate your app
✅ Report gets generated
✅ HTML report shows findings (or "no bugs found")

**That's it! You're now running autonomous testing!** 🎉

---

Need more details? See **README.md** for comprehensive documentation.
