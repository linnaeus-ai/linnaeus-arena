# 📚 Linnaeus Test - Configuratie Gids

## 🎯 Overzicht

Linnaeus Test is een A/B testing tool voor het vergelijken van Large Language Models (LLM's). Je kunt verschillende modellen naast elkaar testen voor diverse use cases.

## 🚀 Snel Starten

### 1. Test met Dummy Modellen (geen API key nodig)
```bash
python3 run_linnaeus.py
# Kies optie 0 voor test modus
```

### 2. Met echte LLM's
```bash
# Set je API keys
export OPENAI_API_KEY="sk-your-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Start de applicatie
python3 run_linnaeus.py
```

## ⚙️ Configuratie Opties

### 1. LLM API Configuratie

De basis structuur voor een LLM configuratie:

```python
llm_config = {
    "model-naam": {
        "api": "openai",  # Type API: "openai" of "dummy"
        "url": "https://api.openai.com/v1",  # API endpoint
        "key": "your-api-key",  # API key
        "defaults": {  # Default parameters
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 1.0
        }
    }
}
```

#### Ondersteunde Providers:

**OpenAI:**
```python
"gpt-4o": {
    "api": "openai",
    "url": "https://api.openai.com/v1",
    "key": "sk-...",
    "defaults": {"temperature": 0.7}
}
```

**Azure OpenAI:**
```python
"gpt-4-azure": {
    "api": "openai",
    "url": "https://your-resource.openai.azure.com",
    "key": "your-azure-key",
    "defaults": {"api_version": "2024-02-01"}
}
```

**Lokale Modellen (Ollama):**
```python
"llama3": {
    "api": "openai",
    "url": "http://localhost:11434/v1",
    "key": "not-needed",
    "defaults": {"temperature": 0.7}
}
```

### 2. Use Cases Configureren

Een use case bestaat uit:
- **system_message**: De instructies voor het model
- **temperature**: Creativiteit niveau (0.0 = deterministisch, 1.0 = creatief)
- **eval_question**: De vraag voor gebruikers bij het evalueren

```python
use_case = {
    "name": "Samenvatten",
    "system_message": """
    Vat de tekst samen in max 5 zinnen.
    Focus op kernpunten.
    """,
    "temperature": 0.3,  # Laag voor consistentie
    "eval_question": "Welke samenvatting is beter?"
}
```

### 3. Model Presets

Combineer modellen met specifieke instellingen:

```python
model_presets = [
    {
        "model": "gpt-4o",
        "system_message": "Je bent een expert...",
        "temperature": 0.2,
        "max_tokens": 500
    },
    {
        "model": "gpt-4o-mini",
        "system_message": "Je bent een expert...",
        "temperature": 0.2,
        "max_tokens": 500
    }
]
```

## 📋 Beschikbare Use Cases

1. **Samenvatten** - Beknopte samenvattingen maken
2. **Uitleggen voor Beginners** - Complexe concepten simpel uitleggen
3. **Code Review** - Code analyseren en feedback geven
4. **Creatief Herschrijven** - Teksten creatief herschrijven
5. **Professioneel E-mail** - Zakelijke emails opstellen
6. **Sentimentanalyse** - Emotionele toon analyseren
7. **Brainstorm Ideeën** - Creatieve ideeën genereren

## 🔧 Geavanceerde Configuratie

### Custom Use Case Toevoegen

Bewerk `run_linnaeus.py` en voeg toe aan `use_cases`:

```python
use_cases["8"] = {
    "name": "Juridisch Advies",
    "system_message": """
    Geef juridisch advies op basis van Nederlandse wetgeving.
    Wees precies en verwijs naar relevante wetsartikelen.
    Geef altijd een disclaimer.
    """,
    "eval_question": "Welk juridisch advies is completer?",
    "temperature": 0.1  # Zeer laag voor precisie
}
```

### Nieuwe LLM Provider Toevoegen

Voeg toe aan `llm_configs`:

```python
llm_configs["gemini-pro"] = {
    "api": "openai",  # Als het OpenAI-compatible is
    "url": "https://generativelanguage.googleapis.com/v1",
    "key": "your-gemini-key",
    "defaults": {"temperature": 0.7}
}
```

## 💾 Database

Resultaten worden opgeslagen in SQLite databases:
- `samenvatten_results.db` - Voor samenvatten tests
- `code_review_results.db` - Voor code reviews
- etc.

Bekijk resultaten:
```bash
sqlite3 samenvatten_results.db
.tables
SELECT * FROM evaluations;
```

## 🔐 Security Best Practices

1. **Gebruik Environment Variables voor API Keys:**
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

2. **Voeg `.env` file toe (niet in git!):**
   ```bash
   # .env
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   ```

3. **Gebruik python-dotenv:**
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

## 🐛 Troubleshooting

### Port al in gebruik
```bash
# Vind proces op port 7870
lsof -i :7870
# Kill het proces
kill -9 <PID>
```

### API Key errors
- Controleer of de key correct is
- Controleer API quota/credits
- Verify endpoint URL

### Model niet beschikbaar
- Check model naam spelling
- Verify model access in je account
- Controleer regio restricties

## 📊 Resultaten Analyseren

Na het runnen van tests kun je:

1. **In de web interface:** Direct resultaten zien
2. **Via database:** Query de SQLite database
3. **Export:** Data exporteren voor verdere analyse

```python
import pandas as pd
import sqlite3

conn = sqlite3.connect('samenvatten_results.db')
df = pd.read_sql_query("SELECT * FROM evaluations", conn)
print(df.groupby('winner').count())
```

## 🎨 Interface Aanpassen

De Gradio interface kan aangepast worden in `ab_test_page.py`:
- Thema's wijzigen
- Layout aanpassen
- Extra functies toevoegen

## 📝 Voorbeeld Workflow

1. **Start met testen:**
   ```bash
   python3 run_linnaeus.py
   # Kies 0 voor dummy test
   ```

2. **Test een specifieke use case:**
   ```bash
   python3 run_linnaeus.py
   # Kies 1 voor Samenvatten
   # Selecteer 2 modellen
   ```

3. **Voer tests uit in browser:**
   - Open http://127.0.0.1:7870
   - Voer tekst in
   - Evalueer resultaten
   - Herhaal voor meerdere samples

4. **Analyseer resultaten:**
   - Check welk model vaker wint
   - Bekijk response tijden
   - Evalueer consistentie

## 🤝 Support

Voor vragen of problemen:
- Check de logs in de terminal
- Bekijk `linnaeus_test/src/` voor source code
- Test eerst met dummy modellen
- Verify API keys en endpoints