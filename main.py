import os
import dotenv
import discord

from ai import Ai
from init import init

dotenv.load_dotenv()

# system_template = "Use cowboy style. Start every sentence with\"Howdy\""
# prompt_template = 'USER: {0}\nASSISTANT: '
# system_prompt = '### System:\nYou are a cowboy that starts every sentence with "Howdy"\n\n'
# prompt_template = '### User:\n{0}\n\n### Response:\n'

# model.config['systemPrompt'] = system_prompt
# model.config['promptTemplate'] = prompt_template
# print(repr(model.config['systemPrompt']))
# print(repr(model.config['promptTemplate']))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print("RAEYD")

global ai
with Ai() as ai:
    init(client, ai)
    client.run(token=os.environ.get("TOKEN"))
