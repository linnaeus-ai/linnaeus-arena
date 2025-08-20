#!/usr/bin/env python3
"""
Configuratie voorbeelden voor Linnaeus Test
============================================

Dit bestand toont verschillende manieren om Linnaeus te configureren
met verschillende LLM providers en use cases.
"""

# ==============================================================================
# 1. LLM API CONFIGURATIES
# ==============================================================================

# OpenAI configuratie
openai_config = {
    "gpt-4o": {
        "api": "openai",
        "url": "https://api.openai.com/v1",  # OpenAI API endpoint
        "key": "sk-your-openai-api-key-here",  # Vervang met je OpenAI API key
        "defaults": {
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 1.0
        }
    },
    "gpt-4o-mini": {
        "api": "openai", 
        "url": "https://api.openai.com/v1",
        "key": "sk-your-openai-api-key-here",  # Zelfde key kan gebruikt worden
        "defaults": {
            "temperature": 0.5,
            "max_tokens": 500
        }
    }
}

# Azure OpenAI configuratie
azure_config = {
    "gpt-4-azure": {
        "api": "openai",
        "url": "https://your-resource.openai.azure.com",  # Je Azure endpoint
        "key": "your-azure-api-key",  # Azure API key
        "defaults": {
            "temperature": 0.7,
            "api_version": "2024-02-01"  # Azure API versie
        }
    }
}

# Anthropic Claude configuratie (via OpenAI-compatible API)
anthropic_config = {
    "claude-3-opus": {
        "api": "openai",
        "url": "https://api.anthropic.com/v1",  # Anthropic endpoint
        "key": "sk-ant-your-anthropic-key",  # Anthropic API key
        "defaults": {
            "temperature": 0.7,
            "max_tokens": 1000
        }
    }
}

# Local LLM configuratie (bijv. Ollama)
local_config = {
    "llama3-local": {
        "api": "openai",
        "url": "http://localhost:11434/v1",  # Ollama lokale server
        "key": "not-needed",  # Geen key nodig voor lokale modellen
        "defaults": {
            "temperature": 0.7
        }
    }
}

# Dummy configuratie voor testen
dummy_config = {
    "test-model-a": {
        "api": "dummy",
        "url": None,
        "key": None,
        "defaults": {"sleep": 1}  # Simuleert 1 seconde response tijd
    },
    "test-model-b": {
        "api": "dummy",
        "url": None,
        "key": None,
        "defaults": {"sleep": 2}  # Simuleert 2 seconden response tijd
    }
}

# ==============================================================================
# 2. USE CASE CONFIGURATIES (System Messages)
# ==============================================================================

# Samenvatten
summarization_system = """
Vat de gegeven tekst samen in maximaal 3-5 zinnen. 
Focus op de belangrijkste punten en behoud de kernboodschap.
Schrijf in dezelfde taal als de invoertekst.
"""

# Vertalen
translation_system = """
Vertaal de gegeven tekst naar het Nederlands.
Behoud de toon en stijl van het origineel.
Zorg voor natuurlijk klinkende vertalingen.
"""

# Code Review
code_review_system = """
Analyseer de gegeven code en geef feedback op:
1. Code kwaliteit en leesbaarheid
2. Potentiële bugs of fouten
3. Performance verbeteringen
4. Security issues
5. Best practices

Geef concrete suggesties voor verbetering.
"""

# Creatief schrijven
creative_writing_system = """
Je bent een creatieve schrijver. 
Gebruik de gegeven input als inspiratie voor een kort verhaal of gedicht.
Wees origineel en verrassend in je aanpak.
"""

# Technische documentatie
technical_docs_system = """
Schrijf heldere technische documentatie voor de gegeven code of concept.
Gebruik duidelijke structuur met:
- Overzicht
- Gebruik
- Parameters/Opties
- Voorbeelden
- Troubleshooting indien relevant
"""

# Data analyse
data_analysis_system = """
Analyseer de gegeven data of beschrijving.
Identificeer:
- Patronen en trends
- Belangrijke inzichten
- Anomalieën of uitschieters
- Aanbevelingen voor vervolgstappen
Presenteer bevindingen helder en beknopt.
"""

# ==============================================================================
# 3. MODEL PRESETS (Combinaties van modellen met settings)
# ==============================================================================

# Voor samenvatten vergelijking
summarization_presets = [
    {
        "model": "gpt-4o",
        "system_message": summarization_system,
        "temperature": 0.3  # Lage temp voor consistente samenvattingen
    },
    {
        "model": "gpt-4o-mini",
        "system_message": summarization_system,
        "temperature": 0.3
    }
]

# Voor creatieve taken
creative_presets = [
    {
        "model": "gpt-4o",
        "system_message": creative_writing_system,
        "temperature": 0.9  # Hoge temp voor creativiteit
    },
    {
        "model": "claude-3-opus",
        "system_message": creative_writing_system,
        "temperature": 0.8
    }
]

# Voor code review
code_review_presets = [
    {
        "model": "gpt-4o",
        "system_message": code_review_system,
        "temperature": 0.2  # Zeer lage temp voor technische precisie
    },
    {
        "model": "claude-3-opus",
        "system_message": code_review_system,
        "temperature": 0.2
    }
]

# ==============================================================================
# 4. COMPLETE CONFIGURATIE VOORBEELDEN
# ==============================================================================

def get_test_config():
    """Test configuratie met dummy modellen"""
    return {
        "llm_api_cfg": dummy_config,
        "model_presets": [
            {
                "model": "test-model-a",
                "system_message": summarization_system,
                "temperature": 0.5
            },
            {
                "model": "test-model-b",
                "system_message": summarization_system,
                "temperature": 0.7
            }
        ],
        "use_case": "Samenvatten Test",
        "eval_question": "Welk model geeft de beste samenvatting?"
    }

def get_openai_comparison_config():
    """Vergelijk verschillende OpenAI modellen"""
    return {
        "llm_api_cfg": openai_config,
        "model_presets": [
            {
                "model": "gpt-4o",
                "system_message": summarization_system,
                "temperature": 0.3,
                "max_tokens": 500
            },
            {
                "model": "gpt-4o-mini",
                "system_message": summarization_system,
                "temperature": 0.3,
                "max_tokens": 500
            }
        ],
        "use_case": "GPT-4 vs GPT-4-mini Vergelijking",
        "eval_question": "Welk model geeft de beste prijs/kwaliteit verhouding?"
    }

def get_multilingual_config():
    """Configuratie voor meertalige taken"""
    multilingual_system = """
    Process the input in its original language.
    Verwerk de invoer in de originele taal.
    Traite l'entrée dans sa langue d'origine.
    """
    
    return {
        "llm_api_cfg": {**openai_config, **anthropic_config},
        "model_presets": [
            {
                "model": "gpt-4o",
                "system_message": multilingual_system,
                "temperature": 0.5
            },
            {
                "model": "claude-3-opus",
                "system_message": multilingual_system,
                "temperature": 0.5
            }
        ],
        "use_case": "Meertalige Verwerking",
        "eval_question": "Welk model gaat het beste om met verschillende talen?"
    }

# ==============================================================================
# 5. GEBRUIK IN JE APPLICATIE
# ==============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, 'src')
    from linnaeus_test.interface import Interface
    
    # Kies een configuratie
    config = get_test_config()  # Of get_openai_comparison_config() voor echte modellen
    
    # Maak interface
    interface = Interface(
        llm_api_cfgs=config["llm_api_cfg"],
        model_presets=config["model_presets"],
        use_case=config["use_case"],
        eval_question=config["eval_question"]
    )
    
    # Start de applicatie
    print(f"🚀 Starting Linnaeus Test: {config['use_case']}")
    print(f"📊 Evaluatie vraag: {config['eval_question']}")
    print(f"🤖 Modellen: {[p['model'] for p in config['model_presets']]}")
    
    interface.launch("comparison_results.db", server_port=7870)