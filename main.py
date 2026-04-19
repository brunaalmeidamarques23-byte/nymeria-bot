import discord
import os
import requests
import asyncio
import time

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

# ===== MEMÓRIA =====
memoria = {}

# ===== ANTI-SPAM =====
cooldowns = {}

# ===== ATIVAR / DESATIVAR =====
usuarios_ativos = {}

def pode_responder(user_id):
    agora = time.time()
    if user_id in cooldowns and agora - cooldowns[user_id] < 3:
        return False
    cooldowns[user_id] = agora
    return True

# ===== IA =====
def perguntar_ia(user_id, mensagem):
    historico = memoria.get(user_id, [])

    historico.append({"role": "user", "content": mensagem})
    historico = historico[-6:]  # limite de memória

    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é Nymeria, uma entidade sombria, elegante e sarcástica de um mundo medieval. "
                    "Você fala como uma deusa antiga, misteriosa e poderosa. Nunca seja comum."
                )
            }
        ] + historico
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=20
        )

        if r.status_code == 429:
            return "⚠️ Nymeria foi silenciada pelos deuses momentaneamente..."

        if r.status_code != 200:
            print(r.text)
            return "⚠️ Algo deu errado na conexão com Nymeria."

        resposta = r.json()["choices"][0]["message"]["content"]

        historico.append({"role": "assistant", "content": resposta})
        memoria[user_id] = historico

        return resposta

    except Exception as e:
        print(e)
        return "⚠️ As sombras falharam em responder..."

# ===== EVENTOS =====
@bot.event
async def on_ready():
    print(f"🔥 Nymeria despertou como {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    msg = message.content.lower().strip()

    # ===== LIGAR / DESLIGAR =====
    if msg == "non!":
        usuarios_ativos[user_id] = True
        await message.channel.send("🌑 Nymeria volta a sussurrar para você...")
        return

    if msg == "noff!":
        usuarios_ativos[user_id] = False
        await message.channel.send("🌒 Nymeria se cala nas sombras...")
        return

    # verifica se está ativo
    if not usuarios_ativos.get(user_id, True):
        return

    # ===== COMANDOS RPG =====
    if msg.startswith("!invocar"):
        await message.channel.send("🌑 As sombras se contorcem... Nymeria atende ao chamado.")
        return

    if msg.startswith("!oraculo"):
        await message.channel.send("🔮 O oráculo sussurra verdades ocultas...")
        return

    if msg.startswith("!memoria"):
        mem = memoria.get(user_id, [])
        await message.channel.send(f"🧠 Memória atual: {len(mem)} fragmentos.")
        return

    # ===== IA =====
    if bot.user in message.mentions or msg.startswith("!nymeria"):

        if not pode_responder(user_id):
            await message.channel.send("⏳ Nymeria ignora pressa... aguarde.")
            return

        async with message.channel.typing():
            resposta = await asyncio.to_thread(
                perguntar_ia, user_id, message.content
            )

            await message.channel.send(resposta)

# ===== START =====
bot.run(DISCORD_TOKEN)
