import discord
import os
import requests

# ===== CONFIG =====
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not DISCORD_TOKEN:
    raise Exception("❌ DISCORD_TOKEN não encontrado nas variáveis de ambiente")

if not GROQ_API_KEY:
    raise Exception("❌ GROQ_API_KEY não encontrado nas variáveis de ambiente")

# ===== DISCORD SETUP =====
intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

# ===== IA (GROQ) =====
def perguntar_ia(mensagem):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {
                "role": "system",
                "content": "Você é Nymeria, uma IA sombria, elegante e levemente sarcástica de um mundo medieval de fantasia."
            },
            {
                "role": "user",
                "content": mensagem
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        return "⚠️ Erro ao chamar a IA."

    return response.json()["choices"][0]["message"]["content"]

# ===== EVENTOS =====
@bot.event
async def on_ready():
    print(f"🔥 Nymeria online como {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    msg = message.content.lower()

    # resposta simples
    if msg == "oi":
        await message.channel.send("👁️ Nymeria observa você... diga o que deseja.")
        return

    # chamada da IA
    resposta = perguntar_ia(message.content)
    await message.channel.send(resposta)

# ===== START =====
print("🔄 Iniciando Nymeria...")
bot.run(DISCORD_TOKEN)
