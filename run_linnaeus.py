#!/usr/bin/env python3
"""
Hoofdscript voor Linnaeus Test met verschillende use cases
"""
import sys
import os
sys.path.insert(0, 'src')

from linnaeus_test.interface import Interface

# ==============================================================================
# STAP 1: CONFIGUREER JE API KEYS (of gebruik dummy voor testen)
# ==============================================================================

# Optie A: Gebruik environment variables (aanbevolen voor security)
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "sk-your-key-here")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "sk-ant-your-key-here")

# Optie B: Direct in code (alleen voor testen!)
# OPENAI_KEY = "sk-your-openai-key"
# ANTHROPIC_KEY = "sk-ant-your-anthropic-key"

# ==============================================================================
# STAP 2: DEFINIEER BESCHIKBARE MODELLEN
# ==============================================================================

llm_configs = {
    # OpenAI modellen
    "gpt-4o": {
        "api": "openai",
        "url": "https://api.openai.com/v1",
        "key": OPENAI_KEY,
        "defaults": {"temperature": 0.7}
    },
    "gpt-4o-mini": {
        "api": "openai",
        "url": "https://api.openai.com/v1",
        "key": OPENAI_KEY,
        "defaults": {"temperature": 0.7}
    },
    
    # Dummy modellen voor testen (geen API key nodig)
    "dummy-fast": {
        "api": "dummy",
        "url": None,
        "key": None,
        "defaults": {"sleep": 0.5}
    },
    "dummy-slow": {
        "api": "dummy",
        "url": None,
        "key": None,
        "defaults": {"sleep": 2}
    }
}

# ==============================================================================
# STAP 3: DEFINIEER USE CASES
# ==============================================================================

use_cases = {
    "1": {
        "name": "Samenvatten",
        "system_message": """
        Maak een beknopte samenvatting van de tekst in maximaal 5 zinnen.
        Behoud de belangrijkste informatie en schrijf in dezelfde taal als de input.
        """,
        "eval_question": "Welke samenvatting is beter?",
        "temperature": 0.3
    },
    
    "2": {
        "name": "Uitleggen voor Beginners",
        "system_message": """
        Leg het gegeven concept uit alsof je het aan een 10-jarige uitlegt.
        Gebruik simpele taal, voorbeelden en analogieën.
        Vermijd jargon en technische termen.
        """,
        "eval_question": "Welke uitleg is duidelijker voor beginners?",
        "temperature": 0.7
    },
    
    "3": {
        "name": "Code Review",
        "system_message": """
        Review de gegeven code en geef feedback op:
        1. Bugs of fouten
        2. Performance problemen
        3. Security issues
        4. Code kwaliteit
        5. Suggesties voor verbetering
        
        Wees specifiek en geef concrete voorbeelden.
        """,
        "eval_question": "Welke code review is grondiger en nuttiger?",
        "temperature": 0.2
    },
    
    "4": {
        "name": "Creatief Herschrijven",
        "system_message": """
        Herschrijf de gegeven tekst op een creatieve manier.
        Je mag de stijl, toon en perspectief veranderen.
        Behoud wel de kernboodschap.
        Wees origineel en verrassend.
        """,
        "eval_question": "Welke creatieve versie is beter?",
        "temperature": 0.9
    },
    
    "5": {
        "name": "Professioneel E-mail Opstellen",
        "system_message": """
        Schrijf een professionele email op basis van de gegeven informatie.
        De email moet:
        - Beleefd en zakelijk zijn
        - Duidelijk gestructureerd
        - To-the-point
        - Correct Nederlands/Engels (afhankelijk van input)
        """,
        "eval_question": "Welke email is professioneler?",
        "temperature": 0.5
    },
    
    "6": {
        "name": "Sentimentanalyse",
        "system_message": """
        Analyseer het sentiment van de gegeven tekst.
        Geef aan:
        - Overall sentiment (positief/negatief/neutraal)
        - Emotionele toon
        - Belangrijkste emoties
        - Score van -1 (zeer negatief) tot +1 (zeer positief)
        """,
        "eval_question": "Welke sentimentanalyse is accurater?",
        "temperature": 0.1
    },
    
    "7": {
        "name": "Brainstorm Ideeën",
        "system_message": """
        Genereer 10 creatieve ideeën gebaseerd op de gegeven input.
        De ideeën moeten:
        - Origineel zijn
        - Haalbaar zijn
        - Gevarieerd zijn
        - Kort maar duidelijk beschreven
        """,
        "eval_question": "Welke brainstorm lijst is creatiever en nuttiger?",
        "temperature": 0.8
    }
}

# ==============================================================================
# HOOFDPROGRAMMA
# ==============================================================================

def main():
    print("=" * 60)
    print("🚀 LINNAEUS TEST - LLM A/B Testing Tool")
    print("=" * 60)
    print("\nBeschikbare use cases:")
    for key, case in use_cases.items():
        print(f"  {key}. {case['name']}")
    print("  0. Test met dummy modellen")
    print()
    
    # Kies use case
    choice = input("Kies een use case (0-7): ").strip()
    
    if choice == "0":
        # Test modus met dummy modellen
        selected_models = ["dummy-fast", "dummy-slow"]
        use_case = use_cases["1"]  # Gebruik samenvatten als default
        print("\n✅ Test modus met dummy modellen")
    else:
        if choice not in use_cases:
            print("❌ Ongeldige keuze!")
            return
        
        use_case = use_cases[choice]
        
        # Kies modellen om te vergelijken
        print("\nBeschikbare modellen:")
        available_models = list(llm_configs.keys())
        for i, model in enumerate(available_models, 1):
            print(f"  {i}. {model}")
        
        print("\nKies 2 modellen om te vergelijken")
        model1_idx = int(input("Eerste model (nummer): ")) - 1
        model2_idx = int(input("Tweede model (nummer): ")) - 1
        
        selected_models = [
            available_models[model1_idx],
            available_models[model2_idx]
        ]
    
    # Configureer model presets
    model_presets = []
    for model in selected_models:
        preset = {
            "model": model,
            "system_message": use_case["system_message"],
            "temperature": use_case["temperature"]
        }
        model_presets.append(preset)
    
    # Database naam gebaseerd op use case
    db_name = f"{use_case['name'].lower().replace(' ', '_')}_results.db"
    
    # Start interface
    print("\n" + "=" * 60)
    print(f"📊 Use Case: {use_case['name']}")
    print(f"🤖 Modellen: {selected_models[0]} vs {selected_models[1]}")
    print(f"💾 Database: {db_name}")
    print(f"🌐 Interface start op: http://127.0.0.1:7870")
    print("=" * 60)
    print("\n⚡ Druk op Ctrl+C om te stoppen\n")
    
    # Maak en start interface
    interface = Interface(
        llm_api_cfgs=llm_configs,
        model_presets=model_presets,
        use_case=use_case['name'],
        eval_question=use_case['eval_question']
    )
    
    try:
        interface.launch(db_name, server_port=7870)
    except KeyboardInterrupt:
        print("\n\n👋 Linnaeus Test gestopt")

if __name__ == "__main__":
    main()