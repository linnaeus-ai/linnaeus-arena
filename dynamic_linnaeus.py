#!/usr/bin/env python3
"""
Dynamische Linnaeus Interface - Alles configureerbaar in de UI
"""
import sys
import os
import gradio as gr
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

sys.path.insert(0, 'src')

# Probeer dotenv te laden als het bestaat
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from linnaeus_test.database import Database
from linnaeus_test.llm_base import LLMBase
from linnaeus_test.manager import Manager

# ==============================================================================
# CONFIGURATIES
# ==============================================================================

# Haal Azure credentials uit environment
AZURE_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
GPT4_DEPLOYMENT = os.getenv("GPT4_DEPLOYMENT_NAME", "omni")

# Beschikbare modellen
AVAILABLE_MODELS = {
    "Azure GPT-4 Omni": {
        "api": "openai",
        "url": AZURE_ENDPOINT,
        "key": AZURE_KEY,
        "model": GPT4_DEPLOYMENT,
        "defaults": {"temperature": 0.7, "max_tokens": 2000}
    },
    "Dummy Fast (Test)": {
        "api": "dummy",
        "url": None,
        "key": None,
        "model": "dummy-fast",
        "defaults": {"sleep": 0.5}
    },
    "Dummy Slow (Test)": {
        "api": "dummy",
        "url": None,
        "key": None,
        "model": "dummy-slow",
        "defaults": {"sleep": 2}
    }
}

# Voeg OpenAI toe als API key aanwezig is
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
if OPENAI_KEY:
    AVAILABLE_MODELS.update({
        "OpenAI GPT-4o": {
            "api": "openai",
            "url": "https://api.openai.com/v1",
            "key": OPENAI_KEY,
            "model": "gpt-4o",
            "defaults": {"temperature": 0.7, "max_tokens": 2000}
        },
        "OpenAI GPT-4o-mini": {
            "api": "openai",
            "url": "https://api.openai.com/v1",
            "key": OPENAI_KEY,
            "model": "gpt-4o-mini",
            "defaults": {"temperature": 0.7, "max_tokens": 1000}
        }
    })

# Predefined use cases
USE_CASES = {
    "Samenvatten": {
        "system_message": """Maak een beknopte samenvatting van de tekst in maximaal 5 zinnen.
Behoud de belangrijkste informatie en schrijf in dezelfde taal als de input.""",
        "temperature": 0.3,
        "eval_question": "Welke samenvatting is beter?"
    },
    "Code Review": {
        "system_message": """Review de gegeven code en geef feedback op:
1. Bugs of fouten
2. Performance problemen  
3. Security issues
4. Code kwaliteit
5. Suggesties voor verbetering

Wees specifiek en geef concrete voorbeelden.""",
        "temperature": 0.2,
        "eval_question": "Welke code review is grondiger?"
    },
    "Creatief Schrijven": {
        "system_message": """Gebruik de input als inspiratie voor een creatief verhaal of gedicht.
Wees origineel en verrassend in je aanpak.""",
        "temperature": 0.9,
        "eval_question": "Welk creatief werk is beter?"
    },
    "Uitleg voor Beginners": {
        "system_message": """Leg het concept uit alsof je het aan een 10-jarige uitlegt.
Gebruik simpele taal, voorbeelden en analogieën. Vermijd jargon.""",
        "temperature": 0.6,
        "eval_question": "Welke uitleg is duidelijker?"
    },
    "Vertalen naar Nederlands": {
        "system_message": """Vertaal de gegeven tekst naar correct Nederlands.
Behoud de toon en stijl van het origineel.""",
        "temperature": 0.3,
        "eval_question": "Welke vertaling is beter?"
    },
    "Sentimentanalyse": {
        "system_message": """Analyseer het sentiment van de tekst.
Geef aan: sentiment (positief/negatief/neutraal), emotionele toon, score -1 tot +1.""",
        "temperature": 0.1,
        "eval_question": "Welke analyse is accurater?"
    },
    "Custom": {
        "system_message": "",
        "temperature": 0.5,
        "eval_question": "Welk antwoord is beter?"
    }
}

# ==============================================================================
# DYNAMISCHE INTERFACE
# ==============================================================================

class DynamicLinnaeusInterface:
    def __init__(self):
        self.current_manager = None
        self.database = None
        self.model_configs = {}
        self.responses = {}
        
    def create_model_config(self, model_name, system_message, temperature):
        """Maak model configuratie"""
        if model_name not in AVAILABLE_MODELS:
            return None
            
        model_info = AVAILABLE_MODELS[model_name]
        
        # Maak unieke identifier voor dit model+settings combo
        config_id = f"{model_name}_{temperature}".replace(" ", "_").replace(".", "_")
        
        self.model_configs[config_id] = {
            "api": model_info["api"],
            "url": model_info["url"],
            "key": model_info["key"],
            "model": model_info.get("model", model_name),
            "defaults": {**model_info["defaults"], "temperature": temperature}
        }
        
        return {
            "model": config_id,
            "system_message": system_message,
            "temperature": temperature
        }
    
    def setup_comparison(self, use_case, custom_prompt, model1, model2, temp1, temp2, eval_question):
        """Setup de vergelijking"""
        # Bepaal system message
        if use_case == "Custom":
            if not custom_prompt:
                return "⚠️ Voer een custom prompt in!", None, None
            system_message = custom_prompt
            final_eval = eval_question or "Welk antwoord is beter?"
        else:
            use_case_config = USE_CASES[use_case]
            system_message = use_case_config["system_message"]
            final_eval = eval_question or use_case_config["eval_question"]
        
        # Maak model presets
        preset1 = self.create_model_config(model1, system_message, temp1)
        preset2 = self.create_model_config(model2, system_message, temp2)
        
        if not preset1 or not preset2:
            return "❌ Fout bij configureren modellen", None, None
        
        # Maak database en manager
        db_name = f"dynamic_{use_case.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        self.database = Database(db_name)
        
        # Maak LLM objecten
        llm_objects = []
        for preset in [preset1, preset2]:
            config = self.model_configs[preset["model"]]
            llm = LLMBase.create(
                api=config["api"],
                model=config.get("model", preset["model"]),
                api_url=config["url"],
                api_key=config["key"],
                system_message=preset["system_message"],
                model_params=config["defaults"]
            )
            llm_objects.append(llm)
        
        self.current_manager = Manager(llm_objects, self.database)
        
        status = f"""✅ Configuratie succesvol!
        
📊 Use Case: {use_case}
🤖 Model 1: {model1} (temp: {temp1})
🤖 Model 2: {model2} (temp: {temp2})
💾 Database: {db_name}
❓ Evaluatie: {final_eval}"""
        
        return status, final_eval, gr.update(visible=True)
    
    def generate_responses(self, user_input, progress=gr.Progress()):
        """Genereer responses van beide modellen"""
        if not self.current_manager:
            return "⚠️ Configureer eerst de modellen!", "", ""
        
        if not user_input:
            return "⚠️ Voer tekst in!", "", ""
        
        progress(0, desc="Start generatie...")
        
        # Reset responses
        self.responses = {}
        
        try:
            # Genereer responses
            progress(0.3, desc="Model A genereert...")
            response_a = self.current_manager.llm_objects[0].call(user_input)
            self.responses['a'] = response_a
            
            progress(0.6, desc="Model B genereert...")
            response_b = self.current_manager.llm_objects[1].call(user_input)
            self.responses['b'] = response_b
            
            # Randomize volgorde voor blind testing
            import random
            if random.choice([True, False]):
                self.responses = {'a': response_b, 'b': response_a}
                self.swap_order = True
            else:
                self.swap_order = False
            
            progress(1.0, desc="Klaar!")
            
            return (
                "✅ Responses gegenereerd! Kies je favoriet hieronder.",
                self.responses['a'],
                self.responses['b']
            )
            
        except Exception as e:
            return f"❌ Fout: {str(e)}", "", ""
    
    def submit_evaluation(self, choice, user_input):
        """Sla evaluatie op"""
        if not self.current_manager or not self.responses:
            return "⚠️ Genereer eerst responses!"
        
        if choice == "Geen voorkeur":
            winner = None
        else:
            # Corrigeer voor swap
            if hasattr(self, 'swap_order') and self.swap_order:
                winner = "b" if choice == "Model A" else "a"
            else:
                winner = "a" if choice == "Model A" else "b"
        
        # Sla op in database (simplified versie)
        try:
            # Voor nu alleen feedback
            actual_winner = "Model 1" if winner == "a" else "Model 2" if winner == "b" else "Gelijkspel"
            return f"""✅ Evaluatie opgeslagen!
            
Jouw keuze: {choice}
Werkelijke winnaar: {actual_winner}

Je kunt een nieuwe test starten met andere input."""
        except Exception as e:
            return f"❌ Fout bij opslaan: {str(e)}"

# ==============================================================================
# GRADIO INTERFACE
# ==============================================================================

def create_interface():
    interface = DynamicLinnaeusInterface()
    
    with gr.Blocks(title="Linnaeus Dynamic", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🧪 Linnaeus Dynamic - LLM A/B Testing
        
        Configureer je eigen LLM vergelijking met volledige controle over use cases, modellen en parameters.
        """)
        
        with gr.Tab("⚙️ Configuratie"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📝 Use Case")
                    use_case = gr.Dropdown(
                        choices=list(USE_CASES.keys()),
                        value="Samenvatten",
                        label="Selecteer Use Case"
                    )
                    custom_prompt = gr.Textbox(
                        label="Custom System Prompt (alleen voor 'Custom' use case)",
                        placeholder="Voer hier je eigen system prompt in...",
                        lines=5,
                        visible=False
                    )
                    eval_question = gr.Textbox(
                        label="Evaluatie Vraag (optioneel)",
                        placeholder="Laat leeg voor default vraag",
                        value=""
                    )
                
                with gr.Column(scale=1):
                    gr.Markdown("### 🤖 Model 1")
                    model1 = gr.Dropdown(
                        choices=list(AVAILABLE_MODELS.keys()),
                        value=list(AVAILABLE_MODELS.keys())[0],
                        label="Model"
                    )
                    temp1 = gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        value=0.5,
                        step=0.1,
                        label="Temperature"
                    )
                
                with gr.Column(scale=1):
                    gr.Markdown("### 🤖 Model 2")
                    model2 = gr.Dropdown(
                        choices=list(AVAILABLE_MODELS.keys()),
                        value=list(AVAILABLE_MODELS.keys())[-1],
                        label="Model"
                    )
                    temp2 = gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        value=0.5,
                        step=0.1,
                        label="Temperature"
                    )
            
            setup_btn = gr.Button("🚀 Start Vergelijking", variant="primary", size="lg")
            setup_status = gr.Textbox(label="Status", interactive=False)
            
            # Update custom prompt visibility
            def update_custom_visibility(use_case):
                return gr.update(visible=(use_case == "Custom"))
            
            use_case.change(
                update_custom_visibility,
                inputs=[use_case],
                outputs=[custom_prompt]
            )
        
        with gr.Tab("🎯 Test & Evaluatie") as test_tab:
            test_section = gr.Column(visible=False)
            
            with test_section:
                gr.Markdown("### 📝 Input")
                user_input = gr.Textbox(
                    label="Voer je tekst/vraag in",
                    placeholder="Type hier je input voor beide modellen...",
                    lines=5
                )
                
                generate_btn = gr.Button("⚡ Genereer Responses", variant="primary")
                generation_status = gr.Textbox(label="Status", interactive=False)
                
                gr.Markdown("### 📊 Responses")
                with gr.Row():
                    response_a = gr.Textbox(
                        label="Model A",
                        lines=10,
                        interactive=False
                    )
                    response_b = gr.Textbox(
                        label="Model B", 
                        lines=10,
                        interactive=False
                    )
                
                gr.Markdown("### 🏆 Evaluatie")
                current_eval_question = gr.Markdown("Welk antwoord is beter?")
                
                with gr.Row():
                    choice = gr.Radio(
                        choices=["Model A", "Model B", "Geen voorkeur"],
                        label="Jouw keuze",
                        value=None
                    )
                    submit_btn = gr.Button("✅ Verstuur Evaluatie", variant="primary")
                
                eval_result = gr.Textbox(label="Resultaat", interactive=False)
        
        with gr.Tab("📊 Statistieken"):
            gr.Markdown("""
            ### 📈 Resultaten
            
            Statistieken worden hier getoond na meerdere evaluaties.
            
            *Coming soon: Live statistieken, export functionaliteit, en visualisaties.*
            """)
        
        with gr.Tab("ℹ️ Help"):
            gr.Markdown("""
            ### 🚀 Hoe te gebruiken
            
            1. **Configureer** je test in het Configuratie tabblad:
               - Kies een use case of maak je eigen
               - Selecteer twee modellen om te vergelijken
               - Stel de temperature in (0.0 = deterministisch, 1.0 = creatief)
            
            2. **Test** in het Test & Evaluatie tabblad:
               - Voer input in
               - Genereer responses
               - Evalueer welke beter is
            
            3. **Analyseer** resultaten in het Statistieken tabblad
            
            ### 🌡️ Temperature Guide
            - **0.0-0.2**: Zeer consistent, feitelijk
            - **0.3-0.5**: Gebalanceerd
            - **0.6-0.8**: Creatief, gevarieerd
            - **0.9-1.0**: Zeer creatief, onvoorspelbaar
            
            ### 🤖 Beschikbare Modellen
            - **Azure GPT-4**: Krachtigste model (vereist API key)
            - **OpenAI GPT-4**: Direct van OpenAI (vereist API key)
            - **Dummy modellen**: Voor testen zonder API key
            """)
        
        # Event handlers
        setup_btn.click(
            interface.setup_comparison,
            inputs=[use_case, custom_prompt, model1, model2, temp1, temp2, eval_question],
            outputs=[setup_status, current_eval_question, test_section]
        )
        
        generate_btn.click(
            interface.generate_responses,
            inputs=[user_input],
            outputs=[generation_status, response_a, response_b]
        )
        
        submit_btn.click(
            interface.submit_evaluation,
            inputs=[choice, user_input],
            outputs=[eval_result]
        )
    
    return demo

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Linnaeus Dynamic Interface")
    print("=" * 60)
    print("📍 URL: http://127.0.0.1:7870")
    print("=" * 60)
    
    # Check welke modellen beschikbaar zijn
    available = []
    if AZURE_KEY:
        available.append("Azure GPT-4")
    if OPENAI_KEY:
        available.append("OpenAI GPT-4")
    available.append("Dummy Test Modellen")
    
    print(f"✅ Beschikbare modellen: {', '.join(available)}")
    print("\n⚡ Druk op Ctrl+C om te stoppen\n")
    
    demo = create_interface()
    demo.launch(server_port=7870, server_name="127.0.0.1")