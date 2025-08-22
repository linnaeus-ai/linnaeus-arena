"""
LM Arena - UWV/SVB Edition
A blind comparison platform for language models
"""

import gradio as gr
import sqlite3
import json
import random
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import os
from dotenv import load_dotenv
import openai
# import pandas as pd  # Removed for simplicity
from collections import defaultdict
import math

load_dotenv()

# Database setup
DB_FILE = "lm_arena_results.db"

def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Vergelijkingen tabel
    c.execute('''
        CREATE TABLE IF NOT EXISTS comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            prompt TEXT,
            category TEXT,
            model_a TEXT,
            model_b TEXT,
            response_a TEXT,
            response_b TEXT,
            winner TEXT,
            user_feedback TEXT
        )
    ''')
    
    # Model statistieken tabel voor ELO ratings
    c.execute('''
        CREATE TABLE IF NOT EXISTS model_stats (
            model_name TEXT PRIMARY KEY,
            elo_rating REAL DEFAULT 1500,
            total_battles INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            ties INTEGER DEFAULT 0,
            category_stats TEXT DEFAULT '{}'
        )
    ''')
    
    # Initialize models if not exists
    models = [
        "GPT-4-Turbo", "GPT-4", "GPT-3.5-Turbo", 
        "Claude-3-Opus", "Claude-3-Sonnet", "Claude-3-Haiku",
        "Gemini-Pro", "Gemini-Ultra", 
        "Llama-3-70B", "Llama-3-8B",
        "Mixtral-8x7B", "Mistral-7B",
        "Qwen-72B", "Yi-34B", "Deepseek-Coder"
    ]
    
    for model in models:
        c.execute('''
            INSERT OR IGNORE INTO model_stats (model_name) VALUES (?)
        ''', (model,))
    
    conn.commit()
    conn.close()

def calculate_elo_change(rating_a: float, rating_b: float, winner: str, k: float = 32) -> Tuple[float, float]:
    """Calculate ELO rating changes"""
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    expected_b = 1 - expected_a
    
    if winner == "A":
        score_a, score_b = 1, 0
    elif winner == "B":
        score_a, score_b = 0, 1
    else:  # Tie
        score_a, score_b = 0.5, 0.5
    
    change_a = k * (score_a - expected_a)
    change_b = k * (score_b - expected_b)
    
    return change_a, change_b

def update_elo_ratings(model_a: str, model_b: str, winner: str, category: str):
    """Update ELO ratings after a battle"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Get current ratings
    c.execute('SELECT elo_rating, category_stats FROM model_stats WHERE model_name = ?', (model_a,))
    rating_a, cat_stats_a = c.fetchone()
    cat_stats_a = json.loads(cat_stats_a) if cat_stats_a else {}
    
    c.execute('SELECT elo_rating, category_stats FROM model_stats WHERE model_name = ?', (model_b,))
    rating_b, cat_stats_b = c.fetchone()
    cat_stats_b = json.loads(cat_stats_b) if cat_stats_b else {}
    
    # Calculate changes
    change_a, change_b = calculate_elo_change(rating_a, rating_b, winner)
    
    # Update overall stats
    if winner == "A":
        c.execute('''
            UPDATE model_stats 
            SET elo_rating = elo_rating + ?, 
                total_battles = total_battles + 1,
                wins = wins + 1
            WHERE model_name = ?
        ''', (change_a, model_a))
        
        c.execute('''
            UPDATE model_stats 
            SET elo_rating = elo_rating + ?, 
                total_battles = total_battles + 1,
                losses = losses + 1
            WHERE model_name = ?
        ''', (change_b, model_b))
        
    elif winner == "B":
        c.execute('''
            UPDATE model_stats 
            SET elo_rating = elo_rating + ?, 
                total_battles = total_battles + 1,
                losses = losses + 1
            WHERE model_name = ?
        ''', (change_a, model_a))
        
        c.execute('''
            UPDATE model_stats 
            SET elo_rating = elo_rating + ?, 
                total_battles = total_battles + 1,
                wins = wins + 1
            WHERE model_name = ?
        ''', (change_b, model_b))
    else:  # Tie
        c.execute('''
            UPDATE model_stats 
            SET elo_rating = elo_rating + ?, 
                total_battles = total_battles + 1,
                ties = ties + 1
            WHERE model_name = ?
        ''', (change_a, model_a))
        
        c.execute('''
            UPDATE model_stats 
            SET elo_rating = elo_rating + ?, 
                total_battles = total_battles + 1,
                ties = ties + 1
            WHERE model_name = ?
        ''', (change_b, model_b))
    
    # Update category-specific stats
    if category not in cat_stats_a:
        cat_stats_a[category] = {"elo": 1500, "battles": 0, "wins": 0, "losses": 0, "ties": 0}
    if category not in cat_stats_b:
        cat_stats_b[category] = {"elo": 1500, "battles": 0, "wins": 0, "losses": 0, "ties": 0}
    
    # Calculate category-specific ELO changes
    cat_change_a, cat_change_b = calculate_elo_change(
        cat_stats_a[category]["elo"], 
        cat_stats_b[category]["elo"], 
        winner
    )
    
    cat_stats_a[category]["elo"] += cat_change_a
    cat_stats_a[category]["battles"] += 1
    cat_stats_b[category]["elo"] += cat_change_b
    cat_stats_b[category]["battles"] += 1
    
    if winner == "A":
        cat_stats_a[category]["wins"] += 1
        cat_stats_b[category]["losses"] += 1
    elif winner == "B":
        cat_stats_a[category]["losses"] += 1
        cat_stats_b[category]["wins"] += 1
    else:
        cat_stats_a[category]["ties"] += 1
        cat_stats_b[category]["ties"] += 1
    
    c.execute('UPDATE model_stats SET category_stats = ? WHERE model_name = ?', 
              (json.dumps(cat_stats_a), model_a))
    c.execute('UPDATE model_stats SET category_stats = ? WHERE model_name = ?', 
              (json.dumps(cat_stats_b), model_b))
    
    conn.commit()
    conn.close()

def get_model_response(model_name: str, prompt: str, category: str) -> str:
    """Get response from a model (currently using Azure OpenAI)"""
    # Using Azure OpenAI for all models with different parameters to simulate variety
    
    # Try Azure OpenAI first, fallback to regular OpenAI
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    if azure_key:
        from openai import AzureOpenAI
        client = AzureOpenAI(
            api_key=azure_key,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://piet.openai.azure.com")
        )
        deployment_name = os.getenv("GPT4_DEPLOYMENT_NAME", "omni")
    else:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        deployment_name = None
    
    # Simulate different models with different parameters
    model_configs = {
        "GPT-4-Turbo": {"model": "gpt-4-turbo-preview", "temperature": 0.7},
        "GPT-4": {"model": "gpt-4", "temperature": 0.7},
        "GPT-3.5-Turbo": {"model": "gpt-3.5-turbo", "temperature": 0.7},
        "Claude-3-Opus": {"model": "gpt-3.5-turbo", "temperature": 0.8},  # Simulated
        "Claude-3-Sonnet": {"model": "gpt-3.5-turbo", "temperature": 0.6},  # Simulated
        "Claude-3-Haiku": {"model": "gpt-3.5-turbo", "temperature": 0.5},  # Simulated
        "Gemini-Pro": {"model": "gpt-3.5-turbo", "temperature": 0.7},  # Simulated
        "Gemini-Ultra": {"model": "gpt-3.5-turbo", "temperature": 0.9},  # Simulated
        "Llama-3-70B": {"model": "gpt-3.5-turbo", "temperature": 0.75},  # Simulated
        "Llama-3-8B": {"model": "gpt-3.5-turbo", "temperature": 0.65},  # Simulated
        "Mixtral-8x7B": {"model": "gpt-3.5-turbo", "temperature": 0.7},  # Simulated
        "Mistral-7B": {"model": "gpt-3.5-turbo", "temperature": 0.6},  # Simulated
        "Qwen-72B": {"model": "gpt-3.5-turbo", "temperature": 0.8},  # Simulated
        "Yi-34B": {"model": "gpt-3.5-turbo", "temperature": 0.7},  # Simulated
        "Deepseek-Coder": {"model": "gpt-3.5-turbo", "temperature": 0.3},  # Simulated
    }
    
    config = model_configs.get(model_name, {"model": "gpt-3.5-turbo", "temperature": 0.7})
    
    # Add category-specific system prompts
    category_prompts = {
        "💻 Programmeren": "Je bent een behulpzame programmeerassistent. Geef duidelijke, beknopte code-oplossingen.",
        "🔢 Wiskunde": "Je bent een wiskundedeskundige. Los problemen stap voor stap op.",
        "📝 Schrijven": "Je bent een creatieve schrijver. Wees boeiend en welsprekend.",
        "🎯 Redeneren": "Je bent een expert in logisch redeneren. Denk stap voor stap.",
        "🌍 Vertalen": "Je bent een professionele vertaler. Wees nauwkeurig en natuurlijk.",
        "📚 Kennis": "Je bent een deskundige assistent. Geef nauwkeurige, gedetailleerde informatie.",
        "🎨 Creatief": "Je bent creatief en fantasierijk. Denk buiten de gebaande paden.",
        "🔬 Wetenschap": "Je bent een wetenschapsexpert. Leg concepten helder en nauwkeurig uit."
    }
    
    system_prompt = category_prompts.get(category, "Je bent een behulpzame assistent.")
    
    try:
        if azure_key and deployment_name:
            # Use Azure OpenAI
            response = client.chat.completions.create(
                model=deployment_name,  # Use deployment name for Azure
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=config["temperature"],
                max_tokens=1000
            )
        else:
            # Use regular OpenAI
            response = client.chat.completions.create(
                model=config["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=config["temperature"],
                max_tokens=1000
            )
        return response.choices[0].message.content
    except Exception as e:
        # Fallback to a dummy response for testing
        return f"[Gesimuleerd {model_name} Antwoord]\n\nDit is een tijdelijk antwoord voor het testen van de arena interface. In productie zou dit een echt antwoord van {model_name} zijn.\n\nOntvangen prompt: {prompt[:100]}...\n\nCategorie: {category}"

def get_leaderboard(category: str = "Algemeen") -> List[List]:
    """Get leaderboard data as list of lists for Gradio DataFrame"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    headers = ["Rang", "Model", "ELO Score", "Gevechten", "Gewonnen", "Verloren", "Gelijk", "Win %"]
    data = []
    
    if category == "Algemeen":
        c.execute('''
            SELECT 
                model_name,
                ROUND(elo_rating, 0) as elo,
                total_battles,
                wins,
                losses,
                ties,
                CASE WHEN total_battles > 0 
                    THEN ROUND(100.0 * wins / total_battles, 1) 
                    ELSE 0 
                END as win_rate
            FROM model_stats
            WHERE total_battles > 0
            ORDER BY elo_rating DESC
        ''')
        
        for idx, row in enumerate(c.fetchall(), 1):
            data.append([idx] + list(row))
    else:
        # Parse category stats from JSON
        c.execute('SELECT model_name, category_stats FROM model_stats')
        
        model_data = []
        for model, cat_stats_json in c.fetchall():
            cat_stats = json.loads(cat_stats_json) if cat_stats_json else {}
            if category in cat_stats and cat_stats[category]["battles"] > 0:
                stats = cat_stats[category]
                model_data.append([
                    model,
                    round(stats["elo"], 0),
                    stats["battles"],
                    stats["wins"],
                    stats["losses"],
                    stats["ties"],
                    round(100.0 * stats["wins"] / stats["battles"], 1) if stats["battles"] > 0 else 0
                ])
        
        # Sort by ELO rating
        model_data.sort(key=lambda x: x[1], reverse=True)
        
        # Add rank
        for idx, row in enumerate(model_data, 1):
            data.append([idx] + row)
    
    conn.close()
    
    if not data:
        return [["No data available for this category"]]
    
    return [headers] + data

# Gradio Interface
def create_arena_interface():
    """Create the main arena interface"""
    
    with gr.Blocks(title="LM Arena - UWV/SVB", theme=gr.themes.Soft()) as demo:
        session_state = gr.State({
            "session_id": hashlib.md5(str(time.time()).encode()).hexdigest(),
            "current_models": None,
            "current_prompt": None,
            "current_category": None,
            "responses": None
        })
        
        gr.Markdown("""
        # ⚔️ LM Arena - UWV/SVB Editie
        
        ### Blind Model Vergelijkingsplatform
        Test en vergelijk taalmodellen in directe gevechten. Modellen blijven verborgen tot na het stemmen!
        """)
        
        with gr.Tabs():
            # Arena Tab
            with gr.TabItem("🎮 Arena"):
                with gr.Row():
                    with gr.Column(scale=1):
                        category_dropdown = gr.Dropdown(
                            choices=[
                                "💻 Programmeren", "🔢 Wiskunde", "📝 Schrijven", 
                                "🎯 Redeneren", "🌍 Vertalen", 
                                "📚 Kennis", "🎨 Creatief", "🔬 Wetenschap"
                            ],
                            value="💻 Programmeren",
                            label="Categorie",
                            interactive=True
                        )
                        
                        model_selector = gr.CheckboxGroup(
                            choices=[
                                "GPT-4-Turbo", "GPT-4", "GPT-3.5-Turbo",
                                "Claude-3-Opus", "Claude-3-Sonnet", "Claude-3-Haiku",
                                "Gemini-Pro", "Gemini-Ultra",
                                "Llama-3-70B", "Llama-3-8B",
                                "Mixtral-8x7B", "Mistral-7B",
                                "Qwen-72B", "Yi-34B", "Deepseek-Coder"
                            ],
                            value=["GPT-4-Turbo", "GPT-3.5-Turbo"],
                            label="Selecteer Modellen voor Gevecht (2 worden willekeurig gekozen)",
                            interactive=True
                        )
                        
                        prompt_input = gr.Textbox(
                            lines=5,
                            placeholder="Voer hier je prompt in...\n\nVoorbeeld: Schrijf een Python functie om de Fibonacci reeks te berekenen",
                            label="Prompt"
                        )
                        
                        submit_btn = gr.Button("⚔️ Start Gevecht", variant="primary", size="lg")
                        clear_btn = gr.Button("🔄 Wissen", variant="secondary")
                    
                    with gr.Column(scale=2):
                        with gr.Row():
                            with gr.Column():
                                model_a_label = gr.Markdown("### 🤖 Model A")
                                response_a = gr.Textbox(
                                    lines=15,
                                    label="Antwoord A",
                                    interactive=False
                                )
                            
                            with gr.Column():
                                model_b_label = gr.Markdown("### 🤖 Model B")
                                response_b = gr.Textbox(
                                    lines=15,
                                    label="Antwoord B",
                                    interactive=False
                                )
                        
                        with gr.Row():
                            vote_a_btn = gr.Button("👈 A is beter", variant="primary", interactive=False)
                            vote_tie_btn = gr.Button("🤝 Gelijkspel", variant="secondary", interactive=False)
                            vote_b_btn = gr.Button("👉 B is beter", variant="primary", interactive=False)
                            vote_both_bad_btn = gr.Button("👎 Beide zijn slecht", variant="stop", interactive=False)
                        
                        result_message = gr.Markdown("")
                        
                        with gr.Row():
                            regenerate_btn = gr.Button("🔄 Opnieuw genereren", interactive=False)
                            share_btn = gr.Button("📤 Delen", interactive=False)
            
            # Leaderboard Tab
            with gr.TabItem("🏆 Ranglijst"):
                gr.Markdown("""
                ## Globale Ranglijst
                Rankings gebaseerd op ELO-beoordelingssysteem (vergelijkbaar met schaakratings)
                """)
                
                with gr.Row():
                    leaderboard_category = gr.Dropdown(
                        choices=[
                            "Algemeen", "💻 Programmeren", "🔢 Wiskunde", "📝 Schrijven", 
                            "🎯 Redeneren", "🌍 Vertalen", 
                            "📚 Kennis", "🎨 Creatief", "🔬 Wetenschap"
                        ],
                        value="Algemeen",
                        label="Categorie Filter"
                    )
                    refresh_btn = gr.Button("🔄 Vernieuwen", variant="secondary")
                
                leaderboard_table = gr.DataFrame(
                    value=get_leaderboard("Algemeen"),
                    label="Model Ranglijst"
                )
                
                gr.Markdown("""
                ### 📊 Statistieken
                - **ELO Score**: Prestatiescore (hoger is beter, begint bij 1500)
                - **Win Percentage**: Percentage gewonnen gevechten
                - **Gevechten**: Totaal aantal vergelijkingen
                """)
            
            # Over Tab
            with gr.TabItem("ℹ️ Over"):
                gr.Markdown("""
                ## Over LM Arena - UWV/SVB Editie
                
                Dit platform maakt blinde vergelijking van taalmodellen mogelijk voor onbevooroordeelde evaluatie.
                
                ### Hoe het werkt:
                1. **Selecteer modellen**: Kies 2 of meer modellen voor de gevechtspool
                2. **Voer prompt in**: Typ je vraag of taak
                3. **Blinde evaluatie**: Twee modellen worden willekeurig geselecteerd en hun antwoorden getoond (identiteit verborgen)
                4. **Stem**: Kies welk antwoord beter is
                5. **Onthulling**: Model-identiteiten worden getoond na het stemmen
                6. **ELO update**: Rankings worden bijgewerkt op basis van resultaten
                
                ### Categorieën:
                - **💻 Programmeren**: Programmeer- en softwareontwikkelingstaken
                - **🔢 Wiskunde**: Wiskundige problemen en berekeningen
                - **📝 Schrijven**: Creatief en professioneel schrijven
                - **🎯 Redeneren**: Logisch redeneren en probleemoplossing
                - **🌍 Vertalen**: Taalvertaaltaken
                - **📚 Kennis**: Algemene kennis en feitelijke vragen
                - **🎨 Creatief**: Creatieve en fantasierijke taken
                - **🔬 Wetenschap**: Wetenschappelijke uitleg en concepten
                
                ### ELO Beoordelingssysteem:
                - Vergelijkbaar met schaakrankings
                - Begint bij 1500 punten
                - Winnen van sterkere tegenstanders = meer punten verdiend
                - Verliezen van zwakkere tegenstanders = meer punten verloren
                
                ---
                *Gebouwd voor UWV/SVB - Aangedreven door Linnaeus AI*
                """)
        
        # Event handlers
        def start_battle(prompt, category, selected_models, state):
            if not prompt:
                return (
                    gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(value="⚠️ Voer een prompt in!"),
                    gr.update(), gr.update(), gr.update(), gr.update(),
                    state
                )
            
            if len(selected_models) < 2:
                return (
                    gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(value="⚠️ Selecteer minimaal 2 modellen!"),
                    gr.update(), gr.update(), gr.update(), gr.update(),
                    state
                )
            
            # Randomly select 2 models
            battle_models = random.sample(selected_models, 2)
            random.shuffle(battle_models)  # Randomize position
            
            # Get responses
            response_a_text = get_model_response(battle_models[0], prompt, category)
            response_b_text = get_model_response(battle_models[1], prompt, category)
            
            # Update state
            state["current_models"] = battle_models
            state["current_prompt"] = prompt
            state["current_category"] = category
            state["responses"] = [response_a_text, response_b_text]
            
            return (
                gr.update(value="### 🤖 Model A (Verborgen)"),
                gr.update(value=response_a_text),
                gr.update(value="### 🤖 Model B (Verborgen)"),
                gr.update(value=response_b_text),
                gr.update(value=""),
                gr.update(interactive=True),  # vote_a
                gr.update(interactive=True),  # vote_tie
                gr.update(interactive=True),  # vote_b
                gr.update(interactive=True),  # vote_both_bad
                state
            )
        
        def vote(winner, state):
            if not state["current_models"]:
                return gr.update(value="⚠️ Geen actief gevecht!"), state
            
            model_a, model_b = state["current_models"]
            
            # Map vote to winner
            if winner == "A":
                winner_model = "A"
            elif winner == "B":
                winner_model = "B"
            elif winner == "tie":
                winner_model = "tie"
            else:  # both_bad
                winner_model = "tie"  # Treat as tie for ELO
            
            # Save to database
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('''
                INSERT INTO comparisons (
                    session_id, prompt, category, model_a, model_b,
                    response_a, response_b, winner
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                state["session_id"], state["current_prompt"], state["current_category"],
                model_a, model_b, state["responses"][0], state["responses"][1],
                winner_model
            ))
            conn.commit()
            conn.close()
            
            # Update ELO ratings
            update_elo_ratings(model_a, model_b, winner_model, state["current_category"])
            
            # Reveal models
            result_text = f"""
            ### 🎭 Modellen Onthuld!
            
            **Model A**: {model_a}  
            **Model B**: {model_b}
            
            **Jouw stem**: {"👈 A is beter" if winner == "A" else "👉 B is beter" if winner == "B" else "🤝 Gelijkspel" if winner == "tie" else "👎 Beide zijn slecht"}
            
            Bedankt voor je feedback! De ranglijst is bijgewerkt.
            """
            
            return gr.update(value=result_text), state
        
        def clear_arena():
            return (
                gr.update(value=""),  # prompt
                gr.update(value="### 🤖 Model A"),  # model_a_label
                gr.update(value=""),  # response_a
                gr.update(value="### 🤖 Model B"),  # model_b_label
                gr.update(value=""),  # response_b
                gr.update(value=""),  # result_message
                gr.update(interactive=False),  # vote_a
                gr.update(interactive=False),  # vote_tie
                gr.update(interactive=False),  # vote_b
                gr.update(interactive=False),  # vote_both_bad
                {"session_id": hashlib.md5(str(time.time()).encode()).hexdigest()}
            )
        
        # Connect events
        submit_btn.click(
            fn=start_battle,
            inputs=[prompt_input, category_dropdown, model_selector, session_state],
            outputs=[
                model_a_label, response_a, model_b_label, response_b,
                result_message, vote_a_btn, vote_tie_btn, vote_b_btn, vote_both_bad_btn,
                session_state
            ]
        )
        
        vote_a_btn.click(
            fn=lambda s: vote("A", s),
            inputs=[session_state],
            outputs=[result_message, session_state]
        )
        
        vote_b_btn.click(
            fn=lambda s: vote("B", s),
            inputs=[session_state],
            outputs=[result_message, session_state]
        )
        
        vote_tie_btn.click(
            fn=lambda s: vote("tie", s),
            inputs=[session_state],
            outputs=[result_message, session_state]
        )
        
        vote_both_bad_btn.click(
            fn=lambda s: vote("both_bad", s),
            inputs=[session_state],
            outputs=[result_message, session_state]
        )
        
        clear_btn.click(
            fn=clear_arena,
            outputs=[
                prompt_input, model_a_label, response_a, model_b_label, response_b,
                result_message, vote_a_btn, vote_tie_btn, vote_b_btn, vote_both_bad_btn,
                session_state
            ]
        )
        
        refresh_btn.click(
            fn=get_leaderboard,
            inputs=[leaderboard_category],
            outputs=[leaderboard_table]
        )
        
        leaderboard_category.change(
            fn=get_leaderboard,
            inputs=[leaderboard_category],
            outputs=[leaderboard_table]
        )
    
    return demo

if __name__ == "__main__":
    # Initialize database
    init_database()
    
    # Create and launch interface
    demo = create_arena_interface()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7871,
        share=False,
        debug=True
    )