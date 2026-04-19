import discord
import os
import requests
import asyncio

# ===== CONFIG =====
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not DISCORD_TOKEN:
    raise Exception("❌ DISCORD_TOKEN não encontrado")

if not GROQ_API_KEY:
    raise Exception("❌ GROQ_API_KEY não encontrado")

# ===== DISCORD =====
intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

# ===== IA (RODA EM THREAD PRA NÃO TRAVAR) =====
def perguntar_ia_sync(mensagem):
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
                "content": "Você é Nymeria, uma IA sombria, elegante e levemente sarcástica."
            },
            {
                "role": "user",
                "content": mensagem
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)

        if response.status_code != 200:
            print("Erro Groq:", response.text)
            return "⚠️ A IA não respondeu corretamente."

        return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print("Erro:", e)
        return "⚠️ Erro ao conectar com a IA."

# versão async
async def perguntar_ia(mensagem):
    return await asyncio.to_thread(perguntar_ia_sync, mensagem)

# ===== EVENTOS =====
@bot.event
async def on_ready():
    print(f"🔥 Nymeria online como {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    msg = message.content.lower()

    if msg == "oi":
        await message.channel.send("👁️ Nymeria observa você...")
        return

    resposta = await perguntar_ia(message.content)
    await message.channel.send(resposta)

# ===== START =====
print("🔄 Iniciando Nymeria...")
bot.run(DISCORD_TOKEN)
