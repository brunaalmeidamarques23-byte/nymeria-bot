import discord
import os

print("🔍 Iniciando Nymeria...")

# 🔑 pega token
TOKEN = os.getenv("DISCORD_TOKEN")
print("TOKEN carregado:", "SIM" if TOKEN else "NÃO")

# ❌ se não tiver token, já para aqui
if not TOKEN:
    raise Exception("❌ DISCORD_TOKEN não encontrado nas variáveis de ambiente")

# ⚙️ intents
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# ✅ conexão
@client.event
async def on_ready():
    print("===================================")
    print(f"🔥 Nymeria ONLINE como {client.user}")
    print("===================================")

# 💬 teste de resposta
@client.event
async def on_message(message):
    if message.author.bot:
        return

    msg = message.content.lower()

    if msg == "!ping":
        await message.channel.send("🏓 Pong!")

    elif msg == "oi":
        await message.channel.send("👁️ Nymeria observa você...")

# 🚀 start
try:
    client.run(TOKEN)
except Exception as e:
    print("❌ ERRO AO INICIAR BOT:")
    print(e)
