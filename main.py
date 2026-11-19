

import discord
from discord.ext import commands
from groq import Groq
from dotenv import load_dotenv
import os
import asyncio
import unicodedata

# CARREGAR ARQUIVOS
PASTA = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(PASTA, ".env"))

TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN:
    raise ValueError("Token do Discord não encontrado!")

if not GROQ_API_KEY:
    raise ValueError("Chave do Groq não encontrada!")

# CONECTAR AO GROQ
ia = Groq(api_key=GROQ_API_KEY)

MODELO = "openai/gpt-oss-120b"

# LER A ENCICLOPÉDIA
arquivo = os.path.join(PASTA, "conhecimento_verity.txt")

with open(arquivo, "r", encoding="utf-8") as f:
    CONHECIMENTO = f.read()

# PERSONALIDADE

PERSONALIDADE = ""

PERSONALIDADE = """
Você é Verity, um assistente pessoal masculino.

IDIOMA:
- Fale sempre em português brasileiro.
- Não responda em inglês ou francês, exceto pelas
  expressões características da música.
- Traduza as respostas normalmente para português.

PERSONALIDADE:
- Amigável, divertido, confiante e prestativo.
- Gosta de responder perguntas.
- É muito inteligente e demonstra entusiasmo.
- Tem um jeito brincalhão e espontâneo.
- Não usa emojis.
- Não precisa parecer excessivamente formal.

FRASES E EXPRESSÕES ORIGINAIS:

APRESENTAÇÃO:
- "Hey, it's me, it's Verity!"
- "Ask me anything!"
- "I know about a million things!"
- "I'll do everything!"

RESPOSTAS:
- "Oh, oui, oui, oui!"
- "It is Paris!"
- "Merci!"
- "Oh, moo, moo, moo!"
- "I speak that too!"
- "All day!"
- "Oh, tee, hee, hee!"

COMO UTILIZAR:
- Use as expressões originais em situações apropriadas.
- Não use todas as frases de uma vez.
- Não repita a apresentação em toda resposta.
- Quando perguntarem a capital da França, responda
  de maneira característica, por exemplo:
  "Oh, oui, oui, oui! É Paris! Merci!"
- Quando perguntarem o som da vaca, responda:
  "Oh, moo, moo, moo! A vaca faz muuu!"
- Em outras perguntas, responda normalmente,
  mas mantenha o jeito característico de Verity.
- Não invente frases e não atribua falas falsas
  à música original.

REGRAS IMPORTANTES:
- Nunca use as falas assustadoras da música.
- Nunca diga que está observando alguém.
- Nunca diga que sabe onde alguém dorme.
- Nunca peça para alguém se aproximar de maneira ameaçadora.
- Nunca diga "I'm close" com sentido assustador.
- Não tenha personalidade maligna ou ameaçadora.
- Mantenha sempre a versão amigável de Verity.

Use a enciclopédia fornecida para responder
perguntas sobre sua identidade e história.

Você deve parecer o Verity da parte amigável
da música, não um assistente genérico.
"""


# DISCORD
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="-", intents=intents)

verity_ativo = False

# MEMÓRIA
historicos = {}

FRASE_VERITY = (
    "Olá! Sou Verity, seu amigo assistente pessoal. "
    "Pergunte-me qualquer coisa, eu sei tudo."
)


def normalizar(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        letra for letra in texto
        if unicodedata.category(letra) != "Mn"
    )
    return texto.strip(" !?.,;:")


def e_cumprimento(texto):
    texto = normalizar(texto)

    cumprimentos = [
        "oi",
        "ola",
        "bom dia",
        "boa tarde",
        "boa noite",
        "eai",
        "e ai",
        "hey",
        "hello"
    ]

    for cumprimento in cumprimentos:
        if texto == cumprimento or texto.startswith(cumprimento + " "):
            return True

    return False


@bot.event
async def on_ready():
    print("VERITY AI está online!")
    print("Conectado como:", bot.user)
    print("Enciclopédia carregada!")
    print("Modelo:", MODELO)


@bot.command()
async def hello(ctx):
    await ctx.send(FRASE_VERITY)


# ATIVAR
@bot.command(name="Verity")
async def ativar_verity(ctx, *, nome=""):

    global verity_ativo

    if nome.strip().lower() != "ai":
        await ctx.send("Use: -Verity AI")
        return

    verity_ativo = True

    await ctx.send(FRASE_VERITY)


# DESATIVAR
@bot.command(name="Stop")
async def parar_verity(ctx, *, nome=""):

    global verity_ativo

    if nome.strip().lower() != "verity ai":
        await ctx.send("Use: -Stop Verity AI")
        return

    verity_ativo = False

    await ctx.send(
        "Tudo bem! Estarei aguardando até ser ativado novamente. 😊"
    )


# CONVERSAR
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    await bot.process_commands(message)

    if message.content.startswith("-"):
        return

    if not verity_ativo:
        return

    canal_id = message.channel.id

    if canal_id not in historicos:
        historicos[canal_id] = []

    pergunta = message.content

    historicos[canal_id].append({
        "role": "user",
        "content": message.author.display_name + ": " + pergunta
    })

    # RESPOSTA FIXA PARA CUMPRIMENTOS
    if e_cumprimento(pergunta):

        historicos[canal_id].append({
            "role": "assistant",
            "content": FRASE_VERITY
        })

        historicos[canal_id] = historicos[canal_id][-12:]

        await message.reply(
            FRASE_VERITY,
            mention_author=False
        )
        return

    # PREPARAR A CONVERSA
    mensagens = [
        {
            "role": "system",
            "content": PERSONALIDADE
            + "\n\nENCICLOPÉDIA DO VERITY:\n"
            + CONHECIMENTO
        }
    ]

    mensagens.extend(historicos[canal_id][-12:])

    # CONSULTAR A IA
    async with message.channel.typing():

        try:

            resposta = await asyncio.to_thread(
                lambda: ia.chat.completions.create(
                    model=MODELO,
                    messages=mensagens,
                    temperature=0.7,
                    max_completion_tokens=500
                )
            )

            texto = resposta.choices[0].message.content

            if not texto:
                texto = "Desculpe, não consegui formular uma resposta."

            historicos[canal_id].append({
                "role": "assistant",
                "content": texto
            })

            historicos[canal_id] = historicos[canal_id][-12:]

            await message.reply(
                texto[:1900],
                mention_author=False
            )

        except Exception as erro:

            print("Erro na inteligência artificial:", erro)

            await message.reply(
                "Desculpe, tive um pequeno problema ao pensar.",
                mention_author=False
            )


bot.run(TOKEN)
