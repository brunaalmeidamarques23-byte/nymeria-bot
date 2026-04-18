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

CANAL_PERMITIDO = None
bot_ativo = True

# =========================
# LEITURA DE ARQUIVOS
# =========================
def ler_arquivo(nome):
    if not os.path.exists(nome):
        return ""
    try:
        with open(nome, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

def carregar_memoria_total():
    return (
        ler_arquivo("nymeria_core.txt") + "\n\n" +
        ler_arquivo("nymeria_estilo.txt") + "\n\n" +
        ler_arquivo("nymeria_lore.txt") + "\n\n" +
        ler_arquivo("nymeria_relacoes.txt")
    )[-8000:]

# =========================
# MEMÓRIA POR USUÁRIO
# =========================
def carregar_memoria_users():
    if not os.path.exists("memoria_usuarios.json"):
        return {}
    try:
        with open("memoria_usuarios.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def salvar_memoria_users(mem):
    with open("memoria_usuarios.json", "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2, ensure_ascii=False)

memoria_users = carregar_memoria_users()

# =========================
# ATUALIZAR MEMÓRIA
# =========================
def atualizar_memoria(user_id, username, mensagem):
    user_id = str(user_id)

    if user_id not in memoria_users:
        memoria_users[user_id] = {
            "nome": username,
            "afinidade": 0,
            "emocao": "neutra",
            "historico": []
        }

    dados = memoria_users[user_id]
    dados["nome"] = username

    msg = mensagem.lower()

    # Afinidade
    if any(p in msg for p in ["amo", "gosto", "adoro", "confio"]):
        dados["afinidade"] += 1
    elif any(p in msg for p in ["odeio", "idiota", "burra", "cala"]):
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
    if len(dados["historico"]) > 6:
        dados["historico"] = dados["historico"][-6:]

    salvar_memoria_users(memoria_users)
    return dados

# =========================
# CHAMADA DA IA
# =========================
def chamar_ia(mensagem, user_id, username):
    memoria_base = carregar_memoria_total()
    dados = atualizar_memoria(user_id, username, mensagem)

    contexto = f"""
Nome: {dados['nome']}
Afinidade: {dados['afinidade']}
Emoção: {dados['emocao']}
Histórico recente: {' | '.join(dados['historico'])}
"""

    prompt_usuario = contexto + "\n\nMensagem recebida: " + mensagem

    payload = [
        {
            "role": "system",
            "content": memoria_base
        },
        {
            "role": "user",
            "content": prompt_usuario
        }
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
                },
                timeout=60
            )

            if r.status_code != 200:
                print("Erro API:", r.text)
                continue

            data = r.json()

            if "choices" in data:
                resposta = data["choices"][0]["message"]["content"].strip()
                if resposta:
                    return resposta

        except Exception as e:
            print("Erro IA:", e)

    return "*Nymeria permanece em silêncio, como se algo tivesse falhado...*"

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

    conteudo = message.content.lower()

    # COMANDOS
    if conteudo == "noff!":
        bot_ativo = False
        await message.channel.send("*Nymeria se desfaz em folhas e sombras...*")
        return

    if conteudo == "non!":
        bot_ativo = True
        await message.channel.send("*Nymeria surge novamente, a presença suave e envolvente...*")
        return

    if not bot_ativo:
        return

    if CANAL_PERMITIDO and message.channel.name != CANAL_PERMITIDO:
        return

    # GATILHO
    if "nymeria" not in conteudo and not client.user.mentioned_in(message):
        return

    async with message.channel.typing():
        resposta = await asyncio.to_thread(
            chamar_ia,
            message.content,
            message.author.id,
            message.author.display_name
        )

    # ENVIO
    if len(resposta) <= 2000:
        await message.channel.send(resposta)
    else:
        for i in range(0, len(resposta), 1900):
            await message.channel.send(resposta[i:i+1900])

# =========================
# KEEP ALIVE (Render/Uptime)
# =========================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nymeria alive")

def start_server():
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()

# =========================
# RUN
# =========================
if __name__ == "__main__":
    threading.Thread(target=start_server, daemon=True).start()
    client.run(TOKEN)
