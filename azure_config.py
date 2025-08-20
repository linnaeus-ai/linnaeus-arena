#!/usr/bin/env python3
"""
Azure OpenAI Configuratie voor Linnaeus Test
=============================================
Gebruikt de UWV Azure OpenAI endpoints
"""
import sys
import os
sys.path.insert(0, 'src')

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from linnaeus_test.interface import Interface

# ==============================================================================
# AZURE OPENAI CONFIGURATIE
# ==============================================================================

# Azure credentials from environment variables
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
GPT4_DEPLOYMENT_NAME = os.getenv("GPT4_DEPLOYMENT_NAME", "omni")

# Check if required environment variables are set
if not AZURE_OPENAI_API_KEY:
    print("⚠️  Warning: AZURE_OPENAI_API_KEY not set in environment variables")
    print("Please set it using: export AZURE_OPENAI_API_KEY='your-key-here'")
if not AZURE_OPENAI_ENDPOINT:
    print("⚠️  Warning: AZURE_OPENAI_ENDPOINT not set in environment variables")
    print("Please set it using: export AZURE_OPENAI_ENDPOINT='your-endpoint-here'")

# LLM configuraties voor Azure
azure_llm_config = {
    # GPT-4 Omni via Azure
    "gpt-4-omni": {
        "api": "openai",
        "url": AZURE_OPENAI_ENDPOINT,
        "key": AZURE_OPENAI_API_KEY,
        "defaults": {
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.95
        }
    },
    
    # Zelfde model met andere temperatuur settings voor vergelijking
    "gpt-4-omni-creative": {
        "api": "openai",
        "url": AZURE_OPENAI_ENDPOINT,
        "key": AZURE_OPENAI_API_KEY,
        "defaults": {
            "temperature": 0.9,
            "max_tokens": 2000,
            "top_p": 1.0
        }
    },
    
    "gpt-4-omni-precise": {
        "api": "openai",
        "url": AZURE_OPENAI_ENDPOINT,
        "key": AZURE_OPENAI_API_KEY,
        "defaults": {
            "temperature": 0.2,
            "max_tokens": 2000,
            "top_p": 0.9
        }
    },
    
    # Dummy modellen voor testen/vergelijking
    "dummy-baseline": {
        "api": "dummy",
        "url": None,
        "key": None,
        "defaults": {"sleep": 1}
    }
}

# ==============================================================================
# USE CASES (Nederlands voor UWV context)
# ==============================================================================

use_cases = {
    "1": {
        "name": "WIA Aanvraag Samenvatten",
        "system_message": """
        Je bent een expert in het samenvatten van WIA-aanvragen en medische documenten.
        
        Vat de gegeven informatie samen met focus op:
        1. Medische klachten en beperkingen
        2. Arbeidsverleden en huidige situatie
        3. Impact op dagelijks functioneren
        4. Relevante data en tijdlijnen
        
        Schrijf beknopt maar volledig, max 10 zinnen.
        Gebruik professionele medische en juridische terminologie waar gepast.
        """,
        "eval_question": "Welke samenvatting bevat de meest relevante informatie voor de WIA-beoordeling?",
        "temperature": 0.3
    },
    
    "2": {
        "name": "Klantbrief Opstellen",
        "system_message": """
        Je bent een UWV medewerker die heldere brieven schrijft aan klanten.
        
        Schrijf een brief die:
        - Begrijpelijk is voor alle opleidingsniveaus
        - Vriendelijk maar professioneel is
        - Actiegericht is (wat moet de klant doen?)
        - Compleet is (alle benodigde informatie bevat)
        
        Gebruik de actieve vorm en korte zinnen.
        Vermijd ambtelijk taalgebruik.
        """,
        "eval_question": "Welke brief is duidelijker en klantvriendelijker?",
        "temperature": 0.5
    },
    
    "3": {
        "name": "Arbeidsdeskundig Rapport",
        "system_message": """
        Je bent een arbeidsdeskundige die rapporten opstelt.
        
        Analyseer de gegeven informatie en maak een rapport met:
        1. Functieomschrijving en belastbaarheid
        2. Arbeidsmogelijkheden en beperkingen
        3. Re-integratie mogelijkheden
        4. Loonwaarde bepaling
        5. Conclusie en advies
        
        Wees objectief, feitelijk en onderbouw je conclusies.
        """,
        "eval_question": "Welk rapport is completer en beter onderbouwd?",
        "temperature": 0.2
    },
    
    "4": {
        "name": "Bezwaarschrift Analyseren",
        "system_message": """
        Je bent een juridisch medewerker die bezwaarschriften analyseert.
        
        Identificeer in het bezwaarschrift:
        1. De kern van het bezwaar
        2. Juridische gronden
        3. Aangedragen bewijsstukken
        4. Procedurele aspecten
        5. Sterke en zwakke punten
        
        Geef een objectieve analyse zonder vooringenomenheid.
        """,
        "eval_question": "Welke analyse is grondiger en juridisch relevanter?",
        "temperature": 0.1
    },
    
    "5": {
        "name": "Verzekeringsarts Samenvatting",
        "system_message": """
        Je bent een verzekeringsarts die medische informatie samenvat.
        
        Focus op:
        1. Diagnoses en prognoses
        2. Functionele beperkingen
        3. Behandeling en medicatie
        4. Belastbaarheid voor arbeid
        5. Consistentie in klachtenpatroon
        
        Gebruik medische terminologie correct.
        Wees objectief en evidence-based.
        """,
        "eval_question": "Welke medische samenvatting is accurater en relevanter?",
        "temperature": 0.2
    },
    
    "6": {
        "name": "Klantcontact Logging",
        "system_message": """
        Je maakt een heldere notitie van een klantcontact.
        
        Noteer:
        - Datum en tijd van contact
        - Onderwerp van gesprek
        - Belangrijkste punten besproken
        - Gemaakte afspraken
        - Vervolgacties
        
        Schrijf beknopt maar volledig.
        Gebruik bulletpoints waar mogelijk.
        """,
        "eval_question": "Welke notitie is completer en duidelijker?",
        "temperature": 0.3
    },
    
    "7": {
        "name": "Wetgeving Uitleggen",
        "system_message": """
        Je legt complexe sociale zekerheidswetgeving uit aan klanten.
        
        Leg uit:
        - Wat de wet/regeling inhoudt
        - Wie ervoor in aanmerking komt
        - Welke voorwaarden gelden
        - Hoe de aanvraag werkt
        - Belangrijke termijnen
        
        Gebruik begrijpelijke taal zonder juridisch jargon.
        Geef concrete voorbeelden waar mogelijk.
        """,
        "eval_question": "Welke uitleg is begrijpelijker voor de gemiddelde burger?",
        "temperature": 0.4
    }
}

# ==============================================================================
# HOOFDPROGRAMMA
# ==============================================================================

def main():
    print("=" * 60)
    print("🏢 LINNAEUS TEST - UWV Azure OpenAI")
    print("=" * 60)
    print(f"📍 Endpoint: {AZURE_OPENAI_ENDPOINT}")
    print(f"🤖 Model: GPT-4 Omni ({GPT4_DEPLOYMENT_NAME})")
    print("=" * 60)
    print("\nBeschikbare use cases:")
    for key, case in use_cases.items():
        print(f"  {key}. {case['name']}")
    print("  0. Test met verschillende temperatuur settings")
    print()
    
    choice = input("Kies een use case (0-7): ").strip()
    
    if choice == "0":
        # Vergelijk verschillende temperatuur settings
        selected_use = use_cases["1"]  # Gebruik WIA samenvatting als test
        model_presets = [
            {
                "model": "gpt-4-omni-precise",
                "system_message": selected_use["system_message"],
                "temperature": 0.2
            },
            {
                "model": "gpt-4-omni",
                "system_message": selected_use["system_message"],
                "temperature": 0.7
            }
        ]
        use_case_name = "Temperatuur Vergelijking (0.2 vs 0.7)"
        eval_question = "Welke temperatuur geeft betere resultaten?"
    else:
        if choice not in use_cases:
            print("❌ Ongeldige keuze!")
            return
        
        selected_use = use_cases[choice]
        
        # Vergelijk creatieve vs precieze versie voor de gekozen use case
        print("\nVergelijkingsopties:")
        print("1. Creatief vs Precies (verschillende temperaturen)")
        print("2. Twee runs met zelfde settings (consistentie test)")
        print("3. Azure GPT-4 vs Dummy (performance test)")
        
        compare_choice = input("Kies vergelijking (1-3): ").strip()
        
        if compare_choice == "1":
            model_presets = [
                {
                    "model": "gpt-4-omni-precise",
                    "system_message": selected_use["system_message"],
                    "temperature": 0.2
                },
                {
                    "model": "gpt-4-omni-creative",
                    "system_message": selected_use["system_message"],
                    "temperature": 0.9
                }
            ]
        elif compare_choice == "2":
            model_presets = [
                {
                    "model": "gpt-4-omni",
                    "system_message": selected_use["system_message"],
                    "temperature": selected_use["temperature"]
                },
                {
                    "model": "gpt-4-omni",
                    "system_message": selected_use["system_message"],
                    "temperature": selected_use["temperature"]
                }
            ]
        else:  # compare_choice == "3"
            model_presets = [
                {
                    "model": "gpt-4-omni",
                    "system_message": selected_use["system_message"],
                    "temperature": selected_use["temperature"]
                },
                {
                    "model": "dummy-baseline",
                    "system_message": selected_use["system_message"],
                    "temperature": selected_use["temperature"]
                }
            ]
        
        use_case_name = selected_use["name"]
        eval_question = selected_use["eval_question"]
    
    # Database naam
    db_name = f"azure_{use_case_name.lower().replace(' ', '_')}_results.db"
    
    # Start interface
    print("\n" + "=" * 60)
    print(f"📊 Use Case: {use_case_name}")
    print(f"💾 Database: {db_name}")
    print(f"🌐 Interface start op: http://127.0.0.1:7870")
    print("=" * 60)
    print("\n⚡ Druk op Ctrl+C om te stoppen\n")
    
    # Patch voor Azure endpoint compatibiliteit
    for model_key in azure_llm_config:
        if model_key.startswith("gpt-4"):
            # Azure gebruikt deployment name in plaats van model naam
            azure_llm_config[model_key]["model"] = GPT4_DEPLOYMENT_NAME
    
    # Maak en start interface
    interface = Interface(
        llm_api_cfgs=azure_llm_config,
        model_presets=model_presets,
        use_case=use_case_name,
        eval_question=eval_question
    )
    
    try:
        interface.launch(db_name, server_port=7870)
    except KeyboardInterrupt:
        print("\n\n👋 Azure Linnaeus Test gestopt")
    except Exception as e:
        print(f"\n❌ Fout: {e}")
        print("\nMogelijke oplossingen:")
        print("1. Check of de Azure endpoint bereikbaar is")
        print("2. Verifieer de API key")
        print("3. Controleer de deployment naam")

if __name__ == "__main__":
    main()