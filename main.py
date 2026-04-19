import discord
import os
import json
from groq import Groq

# =========================
# 🔑 CONFIG
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN:
    raise Exception("❌ DISCORD_TOKEN não encontrado")

if not GROQ_API_KEY:
    raise Exception("❌ GROQ_API_KEY não encontrada")

client_ai = Groq(api_key=GROQ_API_KEY)

# =========================
# 📜 MEMÓRIA BASE (.txt)
# =========================
def ler(nome):
    if not os.path.exists(nome):
        return ""
    with open(nome, "r", encoding="utf-8") as f:
        return f.read()

def memoria_base():
    return (
        ler("nymeria_core.txt") +
        ler("nymeria_estilo.txt") +
        ler("nymeria_lore.txt") +
        ler("nymeria_relacoes.txt") +
        ler("nymeria_memoria_rpg.txt")
    )[-8000:]

# =========================
# 🧠 MEMÓRIA USUÁRIOS
# =========================
def carregar_memoria():
    if not os.path.exists("memoria_usuarios.json"):
        return {}
    with open("memoria_usuarios.json", "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_memoria(mem):
    with open("memoria_usuarios.json", "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2, ensure_ascii=False)

# =========================
# 🔥 MEMÓRIA EVENTOS
# =========================
def carregar_eventos():
    if not os.path.exists("memoria_eventos.json"):
        return {}
    with open("memoria_eventos.json", "r", encoding="utf-8") as f:
            return json.load(f)

def salvar_eventos(mem):
    with open("memoria_eventos.json", "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2, ensure_ascii=False)

def adicionar_evento(user_id, evento):
    eventos = carregar_eventos()
    if user_id not in eventos:
        eventos[user_id] = []

    eventos[user_id].append(evento)
    eventos[user_id] = eventos[user_id][-10:]
    salvar_eventos(eventos)

# =========================
# 🧠 ATUALIZA MEMÓRIA
# =========================
def atualizar_memoria(user_id, username, mensagem):
    mem = carregar_memoria()

    if user_id not in mem:
        mem[user_id] = {
            "nome": username,
            "afinidade": 0,
            "emocao": "neutra",
            "historico": []
        }

    dados = mem[user_id]
    msg = mensagem.lower()

    if "amo" in msg or "gosto" in msg:
        dados["afinidade"] += 1
    elif "odeio" in msg:
        dados["afinidade"] -= 1

    if "?" in msg:
        dados["emocao"] = "curiosa"
    else:
        dados["emocao"] = "serena"

    dados["historico"].append(f"{username}: {mensagem}")
    dados["historico"] = dados["historico"][-8:]

    if "ragnar" in msg:
        adicionar_evento(user_id, f"{username} mencionou Ragnar")

    salvar_memoria(mem)
    return dados

# =========================
# 🤖 IA GROQ
# =========================
def chamar_ia(msg, user_id, username):
    base = memoria_base()
    dados = atualizar_memoria(user_id, username, msg)
    eventos = carregar_eventos().get(user_id, [])

    contexto = f"""
Nome: {dados['nome']}
Afinidade: {dados['afinidade']}
Emoção: {dados['emocao']}

Histórico:
{' | '.join(dados['historico'])}

Eventos:
{' | '.join(eventos)}
"""

    prompt = f"""
{contexto}

Mensagem:
{msg}

Responda como Nymeria.
"""

    try:
        resposta = client_ai.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": base},
                {"role": "user", "content": prompt}
            ]
        )

        return resposta.choices[0].message.content

    except Exception as e:
        print("Erro IA:", e)
        return "*Nymeria permanece em silêncio...*"

# =========================
# 💬 DISCORD
# =========================
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"🔥 Nymeria online como {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if "nymeria" not in message.content.lower():
        return

    user_id = str(message.author.id)
    username = message.author.display_name

    async with message.channel.typing():
        resposta = chamar_ia(message.content, user_id, username)

    await message.channel.send(resposta[:2000])

# =========================
# 🚀 START
# =========================
client.run(TOKEN)
    elif msg == "oi":
        await message.channel.send("👁️ Nymeria observa você...")

# 🚀 start
try:
    client.run(TOKEN)
except Exception as e:
    print("❌ ERRO AO INICIAR BOT:")
    print(e)
