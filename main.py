import asyncio
import discord
import requests
import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("OPENROUTER_API_KEY")

MODELOS = [
    "meta-llama/llama-3-8b-instruct:free",
    "openchat/openchat-7b:free"
]

bot_ativo = True

# =========================
# MEMÓRIA BASE (TXT)
# =========================
def ler_arquivo(nome):
    if not os.path.exists(nome):
        return ""
    with open(nome, "r", encoding="utf-8") as f:
        return f.read()

def carregar_memoria_base():
    return (
        ler_arquivo("nymeria_core.txt") + "\n\n" +
        ler_arquivo("nymeria_estilo.txt") + "\n\n" +
        ler_arquivo("nymeria_lore.txt") + "\n\n" +
        ler_arquivo("nymeria_relacoes.txt") + "\n\n" +
        ler_arquivo("nymeria_memoria_rpg.txt")
    )[-8000:]

# =========================
# MEMÓRIA DINÂMICA (JSON)
# =========================
def carregar_memoria_json():
    if not os.path.exists("memoria.json"):
        return []
    try:
        with open("memoria.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def salvar_memoria_json(memoria):
    with open("memoria.json", "w", encoding="utf-8") as f:
        json.dump(memoria, f, ensure_ascii=False, indent=2)

def adicionar_memoria(user, mensagem):
    memoria = carregar_memoria_json()

    memoria.append({
        "user": user,
        "mensagem": mensagem
    })

    # Limite pra não crescer infinito
    memoria = memoria[-50:]

    salvar_memoria_json(memoria)

def pegar_contexto_recente():
    memoria = carregar_memoria_json()
    ultimas = memoria[-10:]

    texto = ""
    for m in ultimas:
        texto += f"{m['user']}: {m['mensagem']}\n"

    return texto.strip()

# =========================
# IA
# =========================
def chamar_ia(mensagem, user):
    memoria_base = carregar_memoria_base()
    contexto = pegar_contexto_recente()

    prompt = f"""
Contexto recente:
{contexto}

Mensagem atual:
{user}: {mensagem}

Responda como Nymeria, continuando naturalmente.
"""

    payload = [
        {"role": "system", "content": memoria_base},
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
# DISCORD
# =========================
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print("Nymeria online.")

@client.event
async def on_message(message):
    global bot_ativo

    if message.author.bot:
        return

    msg = message.content

    if msg.lower() == "noff!":
        bot_ativo = False
        await message.channel.send("*Nymeria se dissolve...*")
        return

    if msg.lower() == "non!":
        bot_ativo = True
        await message.channel.send("*Nymeria retorna...*")
        return

    if not bot_ativo:
        return

    if "nymeria" not in msg.lower():
        return

    user = message.author.display_name

    # salva mensagem do usuário
    adicionar_memoria(user, msg)

    async with message.channel.typing():
        resposta = await asyncio.to_thread(
            chamar_ia,
            msg,
            user
        )

    # salva resposta da Nymeria
    adicionar_memoria("Nymeria", resposta)

    await message.channel.send(resposta[:2000])

# =========================
# KEEP ALIVE
# =========================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"alive")

def server():
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()

# =========================
# RUN
# =========================
if __name__ == "__main__":
    threading.Thread(target=server).start()
    client.run(TOKEN)
