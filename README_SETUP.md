# Linnaeus Arena Setup Guide

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8+
- pip/pip3
- Git

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/linnaeus-ai/linnaeus-arena.git
cd linnaeus-arena

# Install dependencies
pip install gradio pandas python-dotenv
```

### 3. Configuration

#### Environment Variables Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your credentials:
```bash
# Required for Azure OpenAI
AZURE_OPENAI_API_KEY="your-key-here"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
GPT4_DEPLOYMENT_NAME="your-deployment-name"

# Optional for other providers
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
```

3. Load environment variables:
```bash
# Option A: Export manually
export $(cat .env | xargs)

# Option B: Use python-dotenv (automatic in scripts)
```

### 4. Running the Applications

#### Multi-Model Arena (Recommended)
```bash
python3 multi_model_arena.py
```
- Compare multiple models with balanced testing
- Blind evaluation mode
- Automatic pair selection

#### Azure Configuration Tool
```bash
python3 azure_config.py
```
- UWV-specific use cases
- Azure GPT-4 testing

#### Dynamic Interface
```bash
python3 dynamic_linnaeus.py
```
- Fully configurable in UI
- Custom prompts support

## 🔒 Security Notes

- **Never commit `.env` files** - They contain sensitive API keys
- Use `.env.example` as a template for team members
- The `.gitignore` file excludes `.env` and `*.db` files
- Rotate API keys regularly

## 📊 Database Files

The application creates SQLite databases for storing test results:
- `arena_*.db` - Multi-model arena results
- `dynamic_*.db` - Dynamic interface results
- These are excluded from git by default

## 🛠️ Troubleshooting

### API Key Not Found
```
⚠️ Warning: AZURE_OPENAI_API_KEY not set in environment variables
```
**Solution**: Ensure `.env` file exists and contains your key

### Port Already in Use
```
OSError: Cannot find empty port in range: 7870-7870
```
**Solution**: Kill existing process or use different port

### Import Errors
```
ModuleNotFoundError: No module named 'linnaeus_test'
```
**Solution**: Ensure you're running from the repository root directory

## 📚 Additional Documentation

- [Configuration Guide](CONFIGURATIE_GIDS.md) - Detailed configuration options
- [API Documentation](docs/api.md) - API reference (if applicable)

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and test
3. Commit with clear messages
4. Push and create a pull request

## 📝 License

See LICENSE file for details.