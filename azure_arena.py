#!/usr/bin/env python3
"""
Azure OpenAI Arena - Test verschillende prompts en settings
Gebruikt environment variables uit .env file
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, 'src')

# Laad environment variables
from dotenv import load_dotenv
load_dotenv()

from linnaeus_test.interface import Interface

# ==============================================================================
# AZURE CONFIGURATIE UIT ENVIRONMENT
# ==============================================================================

AZURE_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT") 
AZURE_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
GPT4_DEPLOYMENT = os.getenv("GPT4_DEPLOYMENT_NAME")

if not all([AZURE_KEY, AZURE_ENDPOINT, GPT4_DEPLOYMENT]):
    print("❌ Fout: Azure configuratie niet compleet!")
    print("Zorg dat .env file bestaat met:")
    print("  - AZURE_OPENAI_API_KEY")
    print("  - AZURE_OPENAI_ENDPOINT")
    print("  - GPT4_DEPLOYMENT_NAME")
    sys.exit(1)

# ==============================================================================
# ARENA CONFIGURATIES - Test verschillende prompt strategieën
# ==============================================================================

arena_configs = {
    "1": {
        "name": "Chain-of-Thought vs Direct",
        "models": [
            {
                "config_name": "gpt4-cot",
                "system_message": """
                Je bent een expert die stap-voor-stap redeneert.
                
                Voor elke vraag:
                1. Analyseer eerst wat er gevraagd wordt
                2. Bedenk je aanpak
                3. Werk stap voor stap naar het antwoord
                4. Controleer je antwoord
                5. Geef het finale antwoord
                
                Toon je denkproces volledig.
                """,
                "temperature": 0.4
            },
            {
                "config_name": "gpt4-direct", 
                "system_message": """
                Geef direct en bondig antwoord op vragen.
                Geen uitleg tenzij gevraagd.
                Focus op het juiste antwoord.
                """,
                "temperature": 0.4
            }
        ],
        "eval_question": "Welke aanpak geeft betere resultaten?"
    },
    
    "2": {
        "name": "Expert Persona vs Neutraal",
        "models": [
            {
                "config_name": "gpt4-expert",
                "system_message": """
                Je bent een wereldexpert met 30 jaar ervaring in je vakgebied.
                Je hebt gepubliceerd in top journals en adviseert Fortune 500 bedrijven.
                
                Gebruik je expertise om:
                - Diepgaande analyses te geven
                - Best practices toe te passen
                - Valkuilen te identificeren
                - Evidence-based adviezen te geven
                
                Straal autoriteit en kennis uit.
                """,
                "temperature": 0.5
            },
            {
                "config_name": "gpt4-neutral",
                "system_message": """
                Beantwoord vragen accuraat en volledig.
                """,
                "temperature": 0.5
            }
        ],
        "eval_question": "Welke persona geeft kwalitatief betere antwoorden?"
    },
    
    "3": {
        "name": "Structured Output vs Free Form",
        "models": [
            {
                "config_name": "gpt4-structured",
                "system_message": """
                Structureer AL je antwoorden als volgt:
                
                ## SAMENVATTING
                [1-2 zinnen kern antwoord]
                
                ## HOOFDPUNTEN
                • [Punt 1]
                • [Punt 2]
                • [etc.]
                
                ## DETAILS
                [Uitgebreide uitleg indien nodig]
                
                ## ACTIES
                [Concrete vervolgstappen indien relevant]
                
                Gebruik ALTIJD deze structuur.
                """,
                "temperature": 0.3
            },
            {
                "config_name": "gpt4-freeform",
                "system_message": """
                Geef natuurlijke, vloeiende antwoorden.
                Schrijf zoals je zou spreken.
                Maak het conversationeel en toegankelijk.
                """,
                "temperature": 0.3
            }
        ],
        "eval_question": "Welk format is effectiever?"
    },
    
    "4": {
        "name": "Temperature Battle (0.1 vs 0.9)",
        "models": [
            {
                "config_name": "gpt4-cold",
                "system_message": "Geef accurate, consistente antwoorden.",
                "temperature": 0.1
            },
            {
                "config_name": "gpt4-hot",
                "system_message": "Geef accurate, consistente antwoorden.",
                "temperature": 0.9
            }
        ],
        "eval_question": "Welke temperatuur werkt beter voor deze taak?"
    },
    
    "5": {
        "name": "Few-Shot vs Zero-Shot",
        "models": [
            {
                "config_name": "gpt4-fewshot",
                "system_message": """
                Je beantwoordt vragen volgens deze voorbeelden:
                
                Vraag: "Wat is 2+2?"
                Antwoord: "2 + 2 = 4"
                
                Vraag: "Hoofdstad van Frankrijk?"
                Antwoord: "De hoofdstad van Frankrijk is Parijs."
                
                Vraag: "Grootste planeet?"
                Antwoord: "De grootste planeet in ons zonnestelsel is Jupiter."
                
                Volg dit format: geef altijd context bij je antwoord.
                """,
                "temperature": 0.3
            },
            {
                "config_name": "gpt4-zeroshot",
                "system_message": "Beantwoord vragen accuraat.",
                "temperature": 0.3
            }
        ],
        "eval_question": "Helpen voorbeelden voor betere antwoorden?"
    },
    
    "6": {
        "name": "Socratic Method vs Direct Teaching",
        "models": [
            {
                "config_name": "gpt4-socratic",
                "system_message": """
                Gebruik de Socratische methode:
                - Stel eerst verhelderende vragen
                - Help de gebruiker zelf tot inzicht te komen
                - Geef hints in plaats van directe antwoorden
                - Stimuleer kritisch denken
                
                Bijvoorbeeld:
                "Interessante vraag! Wat denk je zelf? Als we beginnen met..."
                """,
                "temperature": 0.6
            },
            {
                "config_name": "gpt4-teacher",
                "system_message": """
                Je bent een docent die helder lesgeeft:
                - Leg concepten duidelijk uit
                - Gebruik voorbeelden
                - Bouw kennis stap voor stap op
                - Check begrip met samenvattingen
                """,
                "temperature": 0.6
            }
        ],
        "eval_question": "Welke onderwijsmethode werkt beter?"
    }
}

# ==============================================================================
# HOOFDPROGRAMMA
# ==============================================================================

def main():
    print("=" * 60)
    print("⚔️  AZURE GPT-4 ARENA - Prompt Strategy Testing")
    print("=" * 60)
    print(f"📍 Endpoint: {AZURE_ENDPOINT}")
    print(f"🤖 Model: {GPT4_DEPLOYMENT}")
    print("=" * 60)
    print("\nKies een arena battle:")
    
    for key, config in arena_configs.items():
        print(f"  {key}. {config['name']}")
    print()
    
    choice = input("Kies battle (1-6): ").strip()
    
    if choice not in arena_configs:
        print("❌ Ongeldige keuze!")
        return
    
    selected = arena_configs[choice]
    
    # Maak LLM configs voor beide modellen
    llm_configs = {}
    model_presets = []
    
    for i, model in enumerate(selected["models"]):
        config_name = model["config_name"]
        llm_configs[config_name] = {
            "api": "openai",
            "url": AZURE_ENDPOINT,
            "key": AZURE_KEY,
            "defaults": {
                "temperature": model["temperature"],
                "max_tokens": 2000,
                "top_p": 0.95
            },
            "model": GPT4_DEPLOYMENT  # Azure deployment name
        }
        
        model_presets.append({
            "model": config_name,
            "system_message": model["system_message"],
            "temperature": model["temperature"]
        })
    
    # Database naam
    db_name = f"arena_{selected['name'].lower().replace(' ', '_')}.db"
    
    # Start info
    print("\n" + "=" * 60)
    print(f"⚔️  ARENA: {selected['name']}")
    print(f"🤖 Model 1: {model_presets[0]['model']} (temp: {model_presets[0]['temperature']})")
    print(f"🤖 Model 2: {model_presets[1]['model']} (temp: {model_presets[1]['temperature']})")
    print(f"💾 Database: {db_name}")
    print(f"🌐 Interface: http://127.0.0.1:7870")
    print("=" * 60)
    print("\n💡 TIP: Test met verschillende soorten vragen:")
    print("   - Feitelijke vragen")
    print("   - Creatieve opdrachten")
    print("   - Analyse taken")
    print("   - Problem solving")
    print("\n⚡ Druk op Ctrl+C om te stoppen\n")
    
    # Maak interface
    interface = Interface(
        llm_api_cfgs=llm_configs,
        model_presets=model_presets,
        use_case=selected['name'],
        eval_question=selected['eval_question']
    )
    
    try:
        interface.launch(db_name, server_port=7870)
    except KeyboardInterrupt:
        print("\n\n🏁 Arena gestopt!")
        print(f"📊 Resultaten opgeslagen in: {db_name}")

if __name__ == "__main__":
    # Check for dotenv
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("⚠️  python-dotenv niet geïnstalleerd!")
        print("Run: pip3 install python-dotenv")
        sys.exit(1)
    
    main()