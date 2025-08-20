#!/usr/bin/env python3
"""
Test script voor Linnaeus - A/B testing tool voor LLM modellen
"""
import sys
sys.path.insert(0, 'src')

from linnaeus_test.interface import Interface

# Configuratie voor dummy LLM's (voor test doeleinden)
llm_api_cfg = {
    "model_a": {
        "api": "dummy",
        "url": None,
        "key": None,
        "defaults": {"sleep": 1}
    },
    "model_b": {
        "api": "dummy", 
        "url": None,
        "key": None,
        "defaults": {"sleep": 2}
    }
}

# Test modellen configuratie
test_subjects = [
    {
        "model": "model_a",
        "system_message": "Je bent een behulpzame assistent die samenvattingen maakt.",
        "temperature": 0.7
    },
    {
        "model": "model_b",
        "system_message": "Je bent een expert in het maken van beknopte samenvattingen.",
        "temperature": 0.5
    }
]

# Start de interface
interface = Interface(
    llm_api_cfgs=llm_api_cfg,
    model_presets=test_subjects,
    use_case="Vergelijk LLM Samenvattingen",
    eval_question="Welk model geeft een betere samenvatting?"
)

print("🚀 Starting Linnaeus Test Interface...")
print("📊 Dit is een A/B testing tool voor het vergelijken van LLM modellen")
print("🌐 De interface zal starten op: http://127.0.0.1:7870")
print("\n⚠️  Let op: Dit gebruikt dummy modellen voor demonstratie")
print("Voor echte LLM's moet je API keys configureren (OpenAI, Anthropic, etc.)\n")

# Launch de Gradio interface
interface.launch("test_database.db", server_port=7870)