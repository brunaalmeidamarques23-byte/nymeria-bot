import discord
import os
import requests
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# =========================
# 🔑 CONFIG
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("OPENROUTER_API_KEY")

MODELOS = [
    "meta-llama/llama-3-8b-instruct:free",
    "openchat/openchat-7b:free"
]

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

    # Afinidade
    if any(p in msg for p in ["amo", "gosto", "confio"]):
        dados["afinidade"] += 1
    elif any(p in msg for p in ["odeio", "idiota"]):
        dados["afinidade"] -= 1

    # Emoção
    if "?" in msg:
        dados["emocao"] = "curiosa"
    elif "!" in msg:
        dados["emocao"] = "intensa"
    else:
        dados["emocao"] = "serena"

    # Histórico
    dados["historico"].append(f"{username}: {mensagem}")
    dados["historico"] = dados["historico"][-8:]

    # Eventos
    if "confio" in msg:
        adicionar_evento(user_id, f"{username} demonstrou confiança")

    if "ragnar" in msg:
        adicionar_evento(user_id, f"{username} mencionou Ragnar")

    salvar_memoria(mem)
    return dados

# =========================
# 🤖 IA
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

    payload = [
        {"role": "system", "content": base},
        {"role": "user", "content": prompt}
    ]

    for modelo in MODELOS:
        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": modelo,
                    "messages": payload,
                    "temperature": 0.9,
                    "max_tokens": 500
                }
            )

            data = r.json()

            if "choices" in data:
                return data["choices"][0]["message"]["content"]

        except:
            continue

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
# 🌐 KEEP ALIVE (Render)
# =========================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nymeria alive")

def server():
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()

# =========================
# 🚀 START
# =========================
if __name__ == "__main__":
    threading.Thread(target=server).start()
    client.run(TOKEN)
