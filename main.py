import discord
from discord.ext import commands
import os
from flask import Flask
import threading

# =========================
# 🔹 KEEP ALIVE (Render)
# =========================
app = Flask('')

@app.route('/')
def home():
    return "Nymeria está viva 👁️"

def run_web():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()

# =========================
# 🔹 CARREGAR MEMÓRIA TXT
# =========================
def load_txt(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

NYMERIA_CORE = load_txt("nymeria_core.txt")
NYMERIA_ESTILO = load_txt("nymeria_estilo.txt")
NYMERIA_LORE = load_txt("nymeria_lore.txt")
NYMERIA_RELACOES = load_txt("nymeria_relacoes.txt")
NYMERIA_MEMORIA = load_txt("nymeria_memoria_rpg.txt")

BASE_CONTEXT = f"""
{NYMERIA_CORE}

{NYMERIA_ESTILO}

{NYMERIA_LORE}

{NYMERIA_RELACOES}

{NYMERIA_MEMORIA}
"""

# =========================
# 🔹 DISCORD BOT
# =========================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Nymeria conectada como {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_msg = message.content

    # resposta simples (teste)
    if "oi" in user_msg.lower():
        await message.channel.send("Nymeria observa você... 👁️")

    # =========================
    # 🔹 OPENROUTER (IA)
    # =========================
    import requests

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "openrouter/auto",
        "messages": [
            {
                "role": "system",
                "content": BASE_CONTEXT
            },
            {
                "role": "user",
                "content": user_msg
            }
        ]
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )

        result = response.json()
        reply = result["choices"][0]["message"]["content"]

        await message.channel.send(reply[:2000])

    except Exception as e:
        print("Erro IA:", e)

    await bot.process_commands(message)

# =========================
# 🔹 INICIAR
# =========================
keep_alive()

TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
