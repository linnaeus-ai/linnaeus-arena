# Linnaeus Arena - Development Memory

## Project Overview
**Repository**: linnaeus-arena (renamed from linnaeus_test)  
**Purpose**: Multi-model LLM A/B testing platform with balanced testing  
**Owner**: Thomas Vedder (thomas.vedder@uwv.nl)  
**Organization**: UWV / Linnaeus AI

## Current Status
- **Active Branch**: `topic/NNVT-397`
- **Pull Request**: #1 (open)
- **Application Running**: `http://127.0.0.1:7870` (multi_model_arena.py)

## Key Features Implemented

### 1. Multi-Model Arena (`multi_model_arena.py`)
- Multi-model selection with checkboxes
- Automated balanced pair selection (always tests least-tested pairs)
- Blind testing (models hidden until after evaluation)
- SQLite database for results storage
- Support for 9+ "fake" open source models (all using GPT-4 under the hood)
- Categories: Proprietary, Open Source, Test

### 2. Azure Integration (`azure_config.py`, `azure_arena.py`)
- Azure OpenAI GPT-4 Omni support
- UWV-specific use cases (WIA, bezwaar, etc.)
- Environment variable configuration (secure)
- Multiple prompt strategy testing

### 3. Dynamic Interface (`dynamic_linnaeus.py`)
- Fully configurable in UI
- Custom prompt support
- Temperature control per model
- Use case selection

### 4. Configuration Management
- `.env` file for credentials (gitignored)
- `.env.example` template for team
- Environment variables for all API keys
- No hardcoded credentials in code

## File Structure
```
linnaeus-arena/
├── src/linnaeus_test/          # Original package (unchanged)
├── multi_model_arena.py        # Main arena application
├── azure_config.py             # Azure-specific configs
├── azure_arena.py              # Azure prompt testing
├── dynamic_linnaeus.py         # Dynamic UI version
├── run_linnaeus.py             # Simple runner
├── config_example.py           # Configuration examples
├── test_linnaeus.py            # Test script
├── CONFIGURATIE_GIDS.md        # Dutch configuration guide
├── README_SETUP.md             # Setup instructions
├── .env                        # API keys (gitignored)
├── .env.example                # Template for env vars
└── CLAUDE.md                   # This file
```

## Environment Configuration

### Required Environment Variables
```bash
AZURE_OPENAI_API_KEY="..."
AZURE_OPENAI_ENDPOINT="https://piet.openai.azure.com"
AZURE_OPENAI_API_VERSION="2024-06-01"
GPT4_DEPLOYMENT_NAME="omni"
```

### Optional
```bash
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
```

## Git Configuration
- **User**: Thomas Vedder
- **Email**: thomas.vedder@uwv.nl
- **Remote**: https://github.com/linnaeus-ai/linnaeus-arena.git

## Technical Decisions

### Import Path Fix
- Changed from `sys.path.insert(0, 'linnaeus_test/src')` to `sys.path.insert(0, 'src')`
- All files now inside repository for proper git tracking

### Security Improvements
- Removed hardcoded API keys after PR review
- Added dotenv loading for automatic env var loading
- Created .env.example as template
- Added .gitignore for sensitive files

### Database Design
- Separate SQLite file per session with timestamp
- Tables: comparisons, model_stats
- Excluded from git via .gitignore

## Current Issues/TODOs
- [ ] External leaderboard needs to be connected to read .db files
- [ ] Real open source models need actual different API endpoints
- [ ] Consider adding model response time tracking
- [ ] Add export functionality for results

## Running the Application

### Quick Start
```bash
cd /Users/werk/Documents/Python/Linnaeus/linnaeus-arena
python3 multi_model_arena.py
# Opens at http://127.0.0.1:7870
```

### Kill Running Process
```bash
lsof -i :7870
kill -9 <PID>
```

## Testing Approach
1. Select multiple models (min 2)
2. Arena automatically selects least-tested pair
3. User evaluates blind (doesn't know which model is A or B)
4. After evaluation, models are revealed
5. System tracks wins/losses/draws per model
6. Balanced testing ensures all pairs get equal tests

## Use Cases Configured
1. 📝 Samenvatten (Summarization)
2. 💻 Code Review
3. 🎨 Creatief Schrijven (Creative Writing)
4. 🔬 Technische Uitleg (Technical Explanation)
5. 🌍 Vertalen (Translation)
6. 💡 Brainstorm
7. 📊 Data Analyse
8. ✉️ Email Opstellen

## Fake Models (All GPT-4)
- 🤖 GPT-4 Omni (real)
- 🦙 Llama-3-70B (fake)
- 🐬 Mixtral-8x7B (fake)
- 🦜 Claude-3-Opus (fake)
- 🦅 Falcon-180B (fake)
- 🌟 StarCoder-15B (fake)
- 🧠 WizardLM-70B (fake)
- 🎯 Vicuna-33B (fake)
- 🚀 Gemini-Pro (fake)

Each with slightly different temperature settings to simulate variation.

## PR Feedback Addressed
1. ✅ Removed hardcoded credentials
2. ✅ Added environment variable usage
3. ✅ Created .env.example template
4. ✅ Added setup documentation
5. ✅ Implemented dotenv loading

## Commands Reference
```bash
# Git
git status
git add .
git commit -m "message"
git push origin topic/NNVT-397

# Python
python3 multi_model_arena.py     # Main app
python3 azure_config.py          # Azure specific
python3 dynamic_linnaeus.py      # Dynamic UI

# Process Management
lsof -i :7870                    # Check port
ps aux | grep python             # Find python processes
```

## Notes
- Always run from repository root: `/Users/werk/Documents/Python/Linnaeus/linnaeus-arena`
- The .env file contains real API keys - never commit
- Database files (*.db) are created per session - also gitignored
- All "open source" models currently use GPT-4 for testing purposes

---
*Last updated: 2024-08-20*