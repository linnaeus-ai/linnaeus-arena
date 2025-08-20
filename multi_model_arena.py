#!/usr/bin/env python3
"""
Multi-Model Arena - Test meerdere modellen tegelijk met automatische balancing
"""
import sys
import os
import gradio as gr
import json
import random
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import pandas as pd

sys.path.insert(0, 'src')

# Probeer dotenv te laden
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from linnaeus_test.database import Database
from linnaeus_test.llm_base import LLMBase

# ==============================================================================
# CONFIGURATIES
# ==============================================================================

# Azure credentials
AZURE_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
GPT4_DEPLOYMENT = os.getenv("GPT4_DEPLOYMENT_NAME", "omni")

# Fake open source modellen (allemaal GPT-4 onder de motorkap)
AVAILABLE_MODELS = {
    "🤖 GPT-4 Omni": {
        "api": "openai",
        "url": AZURE_ENDPOINT,
        "key": AZURE_KEY,
        "model": GPT4_DEPLOYMENT,
        "category": "Proprietary",
        "provider": "OpenAI/Azure",
        "params": {"temperature": 0.7, "max_tokens": 2000},
        "description": "Meest geavanceerde model van OpenAI"
    },
    "🦙 Llama-3-70B": {
        "api": "openai",  # Fake - gebruikt eigenlijk GPT-4
        "url": AZURE_ENDPOINT,
        "key": AZURE_KEY,
        "model": GPT4_DEPLOYMENT,
        "category": "Open Source",
        "provider": "Meta",
        "params": {"temperature": 0.65, "max_tokens": 2000},
        "description": "Meta's krachtige open source model"
    },
    "🐬 Mixtral-8x7B": {
        "api": "openai",  # Fake - gebruikt eigenlijk GPT-4
        "url": AZURE_ENDPOINT,
        "key": AZURE_KEY,
        "model": GPT4_DEPLOYMENT,
        "category": "Open Source",
        "provider": "Mistral AI",
        "params": {"temperature": 0.72, "max_tokens": 2000},
        "description": "Mixture of Experts architectuur"
    },
    "🦜 Claude-3-Opus": {
        "api": "openai",  # Fake - gebruikt eigenlijk GPT-4
        "url": AZURE_ENDPOINT,
        "key": AZURE_KEY,
        "model": GPT4_DEPLOYMENT,
        "category": "Proprietary",
        "provider": "Anthropic",
        "params": {"temperature": 0.68, "max_tokens": 2000},
        "description": "Anthropic's meest capabele model"
    },
    "🦅 Falcon-180B": {
        "api": "openai",  # Fake - gebruikt eigenlijk GPT-4
        "url": AZURE_ENDPOINT,
        "key": AZURE_KEY,
        "model": GPT4_DEPLOYMENT,
        "category": "Open Source",
        "provider": "TII",
        "params": {"temperature": 0.75, "max_tokens": 2000},
        "description": "Groot open source model uit UAE"
    },
    "🌟 StarCoder-15B": {
        "api": "openai",  # Fake - gebruikt eigenlijk GPT-4
        "url": AZURE_ENDPOINT,
        "key": AZURE_KEY,
        "model": GPT4_DEPLOYMENT,
        "category": "Open Source",
        "provider": "BigCode",
        "params": {"temperature": 0.3, "max_tokens": 2000},
        "description": "Gespecialiseerd in code generatie"
    },
    "🧠 WizardLM-70B": {
        "api": "openai",  # Fake - gebruikt eigenlijk GPT-4
        "url": AZURE_ENDPOINT,
        "key": AZURE_KEY,
        "model": GPT4_DEPLOYMENT,
        "category": "Open Source", 
        "provider": "Microsoft",
        "params": {"temperature": 0.6, "max_tokens": 2000},
        "description": "Instruction-tuned variant"
    },
    "🎯 Vicuna-33B": {
        "api": "openai",  # Fake - gebruikt eigenlijk GPT-4
        "url": AZURE_ENDPOINT,
        "key": AZURE_KEY,
        "model": GPT4_DEPLOYMENT,
        "category": "Open Source",
        "provider": "LMSYS",
        "params": {"temperature": 0.7, "max_tokens": 2000},
        "description": "Fine-tuned op gebruikersgesprekken"
    },
    "🚀 Gemini-Pro": {
        "api": "openai",  # Fake - gebruikt eigenlijk GPT-4
        "url": AZURE_ENDPOINT,
        "key": AZURE_KEY,
        "model": GPT4_DEPLOYMENT,
        "category": "Proprietary",
        "provider": "Google",
        "params": {"temperature": 0.65, "max_tokens": 2000},
        "description": "Google's multimodal model"
    },
    "⚡ Dummy-Fast": {
        "api": "dummy",
        "url": None,
        "key": None,
        "model": "dummy",
        "category": "Test",
        "provider": "Local",
        "params": {"sleep": 0.5},
        "description": "Test model - snel"
    }
}

# Use cases
USE_CASES = {
    "📝 Samenvatten": {
        "prompt": "Vat de tekst samen in 3-5 zinnen. Focus op kernpunten.",
        "temperature_modifier": -0.2
    },
    "💻 Code Review": {
        "prompt": "Review deze code voor bugs, performance en best practices.",
        "temperature_modifier": -0.3
    },
    "🎨 Creatief Schrijven": {
        "prompt": "Schrijf een creatief verhaal gebaseerd op deze input.",
        "temperature_modifier": 0.2
    },
    "🔬 Technische Uitleg": {
        "prompt": "Leg dit technische concept helder uit.",
        "temperature_modifier": -0.1
    },
    "🌍 Vertalen": {
        "prompt": "Vertaal naar het Nederlands met behoud van toon en stijl.",
        "temperature_modifier": -0.3
    },
    "💡 Brainstorm": {
        "prompt": "Genereer 10 creatieve ideeën gebaseerd op deze input.",
        "temperature_modifier": 0.3
    },
    "📊 Data Analyse": {
        "prompt": "Analyseer deze data en geef inzichten.",
        "temperature_modifier": -0.2
    },
    "✉️ Email Opstellen": {
        "prompt": "Schrijf een professionele email op basis van deze informatie.",
        "temperature_modifier": 0.0
    }
}

# ==============================================================================
# ARENA MANAGER
# ==============================================================================

class MultiModelArena:
    def __init__(self):
        self.selected_models = []
        self.test_statistics = defaultdict(lambda: {"shown": 0, "wins": 0, "losses": 0, "draws": 0})
        self.current_pair = None
        self.current_responses = {}
        self.session_history = []
        self.db_path = f"arena_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        self.init_database()
        
    def init_database(self):
        """Initialiseer database voor statistieken"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                use_case TEXT,
                model_a TEXT,
                model_b TEXT,
                input_text TEXT,
                response_a TEXT,
                response_b TEXT,
                winner TEXT,
                session_id TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_stats (
                model_name TEXT PRIMARY KEY,
                total_shown INTEGER DEFAULT 0,
                total_wins INTEGER DEFAULT 0,
                total_losses INTEGER DEFAULT 0,
                total_draws INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_least_tested_pair(self) -> Tuple[str, str]:
        """Selecteer het minst geteste paar modellen voor balanced testing"""
        if len(self.selected_models) < 2:
            return None, None
        
        # Maak alle mogelijke paren
        pairs = []
        for i, model_a in enumerate(self.selected_models):
            for model_b in self.selected_models[i+1:]:
                # Tel hoe vaak dit paar is getest
                pair_count = 0
                for entry in self.session_history:
                    if (entry['model_a'] == model_a and entry['model_b'] == model_b) or \
                       (entry['model_a'] == model_b and entry['model_b'] == model_a):
                        pair_count += 1
                pairs.append((pair_count, model_a, model_b))
        
        # Sorteer op aantal tests (minst geteste eerst)
        pairs.sort(key=lambda x: x[0])
        
        # Selecteer random uit de minst geteste paren
        min_count = pairs[0][0]
        least_tested = [p for p in pairs if p[0] == min_count]
        selected = random.choice(least_tested)
        
        # Randomize volgorde
        if random.random() > 0.5:
            return selected[1], selected[2]
        else:
            return selected[2], selected[1]
    
    def generate_comparison(self, use_case: str, input_text: str, progress=gr.Progress()):
        """Genereer responses van geselecteerd paar"""
        if not self.selected_models or len(self.selected_models) < 2:
            return "⚠️ Selecteer minstens 2 modellen!", "", "", "", ""
        
        if not input_text:
            return "⚠️ Voer tekst in!", "", "", "", ""
        
        # Selecteer minst geteste paar
        model_a, model_b = self.get_least_tested_pair()
        if not model_a or not model_b:
            return "❌ Fout bij selecteren modellen", "", "", "", ""
        
        self.current_pair = (model_a, model_b)
        
        # Use case settings
        use_case_config = USE_CASES[use_case]
        system_message = use_case_config["prompt"]
        temp_modifier = use_case_config["temperature_modifier"]
        
        progress(0.1, desc="Voorbereiden vergelijking...")
        
        try:
            # Model A
            progress(0.3, desc="Model A genereert...")
            config_a = AVAILABLE_MODELS[model_a]
            
            if config_a["api"] == "dummy":
                response_a = f"[{model_a} Response]\n\nDit is een test response voor de input:\n'{input_text[:100]}...'\n\n" + \
                           f"Use case: {use_case}\nModel parameters: {config_a['params']}"
            else:
                # Adjust temperature
                temp_a = max(0.1, min(1.0, config_a["params"]["temperature"] + temp_modifier))
                
                llm_a = LLMBase.create(
                    api=config_a["api"],
                    model=config_a["model"],
                    api_url=config_a["url"],
                    api_key=config_a["key"],
                    system_message=system_message,
                    model_params={**config_a["params"], "temperature": temp_a}
                )
                response_a = llm_a.call(input_text)
            
            # Model B
            progress(0.6, desc="Model B genereert...")
            config_b = AVAILABLE_MODELS[model_b]
            
            if config_b["api"] == "dummy":
                response_b = f"[{model_b} Response]\n\nDit is een andere test response voor:\n'{input_text[:100]}...'\n\n" + \
                           f"Analyse vanuit {use_case} perspectief\nSettings: {config_b['params']}"
            else:
                temp_b = max(0.1, min(1.0, config_b["params"]["temperature"] + temp_modifier))
                
                llm_b = LLMBase.create(
                    api=config_b["api"],
                    model=config_b["model"],
                    api_url=config_b["url"],
                    api_key=config_b["key"],
                    system_message=system_message,
                    model_params={**config_b["params"], "temperature": temp_b}
                )
                response_b = llm_b.call(input_text)
            
            # Bewaar responses
            self.current_responses = {
                'a': response_a,
                'b': response_b,
                'model_a': model_a,
                'model_b': model_b,
                'use_case': use_case,
                'input': input_text
            }
            
            # Update statistieken
            self.test_statistics[model_a]["shown"] += 1
            self.test_statistics[model_b]["shown"] += 1
            
            progress(1.0, desc="Klaar!")
            
            # Status info
            status = f"""✅ Vergelijking gegenereerd!
            
📊 Use Case: {use_case}
🎯 Blind test - modellen zijn verborgen

Kies hieronder je favoriet zonder te weten welk model wat is."""
            
            return status, response_a, response_b, gr.update(visible=True), gr.update(visible=True)
            
        except Exception as e:
            return f"❌ Fout: {str(e)}", "", "", gr.update(visible=False), gr.update(visible=False)
    
    def submit_evaluation(self, choice: str):
        """Verwerk evaluatie"""
        if not self.current_responses:
            return "⚠️ Genereer eerst een vergelijking!", ""
        
        # Bepaal winnaar
        if choice == "Model A":
            winner = self.current_responses['model_a']
            loser = self.current_responses['model_b']
            winner_key = 'a'
        elif choice == "Model B":
            winner = self.current_responses['model_b']
            loser = self.current_responses['model_a']
            winner_key = 'b'
        else:  # Gelijkspel
            winner = None
            loser = None
            winner_key = 'draw'
        
        # Update statistieken
        if winner:
            self.test_statistics[winner]["wins"] += 1
            self.test_statistics[loser]["losses"] += 1
        else:
            self.test_statistics[self.current_responses['model_a']]["draws"] += 1
            self.test_statistics[self.current_responses['model_b']]["draws"] += 1
        
        # Sla op in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO comparisons (use_case, model_a, model_b, input_text, 
                                    response_a, response_b, winner, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.current_responses['use_case'],
            self.current_responses['model_a'],
            self.current_responses['model_b'],
            self.current_responses['input'],
            self.current_responses['a'],
            self.current_responses['b'],
            winner_key,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        # Voeg toe aan geschiedenis
        self.session_history.append({
            'model_a': self.current_responses['model_a'],
            'model_b': self.current_responses['model_b'],
            'winner': winner_key
        })
        
        # Reveal resultaat
        reveal = f"""🎭 **Onthulling:**

**Model A was:** {self.current_responses['model_a']}
**Model B was:** {self.current_responses['model_b']}

**Jouw keuze:** {choice}
**Winnaar:** {winner if winner else "Gelijkspel"}

📊 **Huidige Stand:**
• {self.current_responses['model_a']}: {self.test_statistics[self.current_responses['model_a']]['wins']} wins, {self.test_statistics[self.current_responses['model_a']]['losses']} losses
• {self.current_responses['model_b']}: {self.test_statistics[self.current_responses['model_b']]['wins']} wins, {self.test_statistics[self.current_responses['model_b']]['losses']} losses"""
        
        return "✅ Evaluatie opgeslagen!", reveal
    
    def get_statistics_table(self):
        """Genereer statistieken tabel"""
        if not self.test_statistics:
            return pd.DataFrame()
        
        data = []
        for model, stats in self.test_statistics.items():
            if stats["shown"] > 0:
                win_rate = (stats["wins"] / stats["shown"]) * 100 if stats["shown"] > 0 else 0
                data.append({
                    "Model": model,
                    "Tests": stats["shown"],
                    "Wins": stats["wins"],
                    "Losses": stats["losses"],
                    "Draws": stats["draws"],
                    "Win Rate": f"{win_rate:.1f}%"
                })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values("Win Rate", ascending=False)
        return df
    
    def get_pair_statistics(self):
        """Krijg statistieken per model paar"""
        pair_stats = defaultdict(lambda: {"count": 0, "balanced": True})
        
        for i, model_a in enumerate(self.selected_models):
            for model_b in self.selected_models[i+1:]:
                count = sum(1 for h in self.session_history 
                          if (h['model_a'] == model_a and h['model_b'] == model_b) or
                             (h['model_a'] == model_b and h['model_b'] == model_a))
                pair_stats[f"{model_a} vs {model_b}"]["count"] = count
        
        return pair_stats

# ==============================================================================
# GRADIO INTERFACE
# ==============================================================================

def create_interface():
    arena = MultiModelArena()
    
    with gr.Blocks(title="Multi-Model Arena", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # ⚔️ Multi-Model Arena - LLM Battle Royale
        
        Test meerdere LLM modellen tegen elkaar met automatische balancing voor eerlijke vergelijking.
        """)
        
        with gr.Tab("🎮 Arena Setup"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📝 Use Case")
                    use_case = gr.Dropdown(
                        choices=list(USE_CASES.keys()),
                        value=list(USE_CASES.keys())[0],
                        label="Selecteer Use Case"
                    )
                
                with gr.Column(scale=2):
                    gr.Markdown("### 🤖 Selecteer Modellen (min. 2)")
                    
                    # Groepeer modellen per categorie
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("**🏢 Proprietary**")
                            proprietary_models = gr.CheckboxGroup(
                                choices=[m for m, info in AVAILABLE_MODELS.items() 
                                        if info["category"] == "Proprietary"],
                                label="",
                                value=[]
                            )
                        
                        with gr.Column():
                            gr.Markdown("**🌍 Open Source**")
                            opensource_models = gr.CheckboxGroup(
                                choices=[m for m, info in AVAILABLE_MODELS.items() 
                                        if info["category"] == "Open Source"],
                                label="",
                                value=[]
                            )
                        
                        with gr.Column():
                            gr.Markdown("**🧪 Test**")
                            test_models = gr.CheckboxGroup(
                                choices=[m for m, info in AVAILABLE_MODELS.items() 
                                        if info["category"] == "Test"],
                                label="",
                                value=[]
                            )
            
            with gr.Row():
                selected_count = gr.Markdown("**Geselecteerd: 0 modellen**")
                confirm_btn = gr.Button("✅ Bevestig Selectie", variant="primary", size="lg")
            
            setup_status = gr.Markdown("")
            
            # Update selected count
            def update_selection(*model_groups):
                all_selected = []
                for group in model_groups:
                    if group:
                        all_selected.extend(group)
                
                arena.selected_models = all_selected
                count = len(all_selected)
                
                if count < 2:
                    return f"**⚠️ Geselecteerd: {count} modellen (min. 2 nodig)**", ""
                else:
                    # Bereken aantal unieke paren
                    num_pairs = (count * (count - 1)) // 2
                    return f"**✅ Geselecteerd: {count} modellen ({num_pairs} unieke paren)**", ""
            
            for checkbox in [proprietary_models, opensource_models, test_models]:
                checkbox.change(
                    update_selection,
                    inputs=[proprietary_models, opensource_models, test_models],
                    outputs=[selected_count, setup_status]
                )
            
            def confirm_selection(*model_groups):
                all_selected = []
                for group in model_groups:
                    if group:
                        all_selected.extend(group)
                
                if len(all_selected) < 2:
                    return "❌ Selecteer minimaal 2 modellen!"
                
                arena.selected_models = all_selected
                num_pairs = (len(all_selected) * (len(all_selected) - 1)) // 2
                
                return f"""✅ **Arena Configuratie Compleet!**
                
🤖 **{len(all_selected)} modellen geselecteerd**
🎯 **{num_pairs} unieke matchups mogelijk**

De arena zal automatisch zorgen voor balanced testing door het minst geteste paar te selecteren.

Ga naar het **Battle** tabblad om te beginnen!"""
            
            confirm_btn.click(
                confirm_selection,
                inputs=[proprietary_models, opensource_models, test_models],
                outputs=[setup_status]
            )
        
        with gr.Tab("⚔️ Battle"):
            gr.Markdown("""
            ### 🎯 Test Arena
            
            De arena selecteert automatisch het minst geteste modelpaar voor balanced vergelijking.
            """)
            
            input_text = gr.Textbox(
                label="Input Tekst",
                placeholder="Voer hier je tekst, vraag of code in...",
                lines=5
            )
            
            generate_btn = gr.Button("⚡ Genereer Battle", variant="primary", size="lg")
            
            battle_status = gr.Markdown("")
            
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
            
            with gr.Row(visible=False) as eval_section:
                choice = gr.Radio(
                    choices=["Model A", "Model B", "Gelijkspel"],
                    label="🏆 Welk antwoord is beter?",
                    value=None
                )
            
            submit_btn = gr.Button("📊 Verstuur Evaluatie", variant="primary", visible=False)
            
            eval_status = gr.Markdown("")
            reveal_text = gr.Markdown("")
            
            # Event handlers
            generate_btn.click(
                lambda uc, txt: arena.generate_comparison(uc, txt),
                inputs=[use_case, input_text],
                outputs=[battle_status, response_a, response_b, eval_section, submit_btn]
            )
            
            submit_btn.click(
                arena.submit_evaluation,
                inputs=[choice],
                outputs=[eval_status, reveal_text]
            )
        
        with gr.Tab("📊 Database Info"):
            gr.Markdown(f"""
            ### 💾 Database Locatie
            
            Alle test resultaten worden opgeslagen in:
            ```
            {arena.db_path}
            ```
            
            Deze database wordt gebruikt door het externe leaderboard voor statistieken en visualisaties.
            
            ### 📈 Huidige Sessie
            """)
            
            session_info = gr.Markdown("")
            refresh_session_btn = gr.Button("🔄 Ververs Sessie Info")
            
            def get_session_info():
                info = f"""
                **Actieve modellen:** {len(arena.selected_models)}
                **Tests deze sessie:** {len(arena.session_history)}
                **Database:** `{arena.db_path}`
                
                **Test Balance:**
                """
                
                if arena.selected_models and len(arena.selected_models) >= 2:
                    pair_stats = arena.get_pair_statistics()
                    for pair, stats in pair_stats.items():
                        info += f"\n• {pair}: {stats['count']} tests"
                    
                    # Check balance
                    counts = [s["count"] for s in pair_stats.values()]
                    if counts and len(counts) > 0:
                        max_diff = max(counts) - min(counts)
                        if max_diff <= 1:
                            info += "\n\n✅ **Perfect gebalanceerd!**"
                        elif max_diff <= 2:
                            info += "\n\n⚠️ **Bijna gebalanceerd**"
                        else:
                            info += "\n\n❌ **Ongebalanceerd - meer tests nodig**"
                
                return info
            
            refresh_session_btn.click(
                get_session_info,
                outputs=[session_info]
            )
        
        with gr.Tab("ℹ️ Info"):
            gr.Markdown("""
            ## 🎮 Hoe werkt de Arena?
            
            ### 1️⃣ **Setup**
            - Kies een use case (bepaalt de prompt)
            - Selecteer minimaal 2 modellen om te testen
            - De arena maakt alle mogelijke paren
            
            ### 2️⃣ **Battle**
            - Voer een tekst/vraag in
            - Arena selecteert automatisch het minst geteste paar
            - Beide modellen genereren een response
            - Je ziet niet welk model wat is (blind test)
            
            ### 3️⃣ **Evaluatie**
            - Kies welk antwoord beter is
            - Na je keuze worden de modellen onthuld
            - Statistieken worden bijgewerkt
            
            ### 4️⃣ **Balancing**
            - Arena zorgt automatisch voor balanced testing
            - Elk modelpaar wordt even vaak getest
            - Voorkomt bias door ongelijke test aantallen
            
            ### 🤖 **Model Categorieën**
            - **Proprietary**: Commerciële modellen (GPT-4, Claude, Gemini)
            - **Open Source**: Vrij beschikbare modellen (Llama, Mixtral, Falcon)
            - **Test**: Dummy modellen voor testen
            
            ### 📊 **Statistieken**
            - **Win Rate**: Percentage gewonnen battles
            - **Balance**: Toont of alle paren evenveel getest zijn
            - Data wordt opgeslagen voor latere analyse
            
            ### 💡 **Tips**
            - Test verschillende soorten input voor betere vergelijking
            - Gebruik minimaal 10 tests per modelpaar voor betrouwbare resultaten
            - Let op: Alle "modellen" gebruiken momenteel GPT-4 onder de motorkap
            """)
    
    return demo

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("⚔️  Multi-Model Arena - LLM Battle Royale")
    print("=" * 60)
    
    if AZURE_KEY:
        print("✅ Azure GPT-4 configured")
    else:
        print("⚠️  No Azure key found - using dummy models only")
    
    print(f"📍 URL: http://127.0.0.1:7870")
    print("=" * 60)
    print("\n💡 TIP: Selecteer meerdere modellen voor automatische balanced testing")
    print("⚡ Druk op Ctrl+C om te stoppen\n")
    
    demo = create_interface()
    demo.launch(server_port=7870, server_name="127.0.0.1")