import discord
from discord.ext import commands
import random
import json


description = '''A music bot'''
bot = commands.Bot(command_prefix='?', description=description)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def track(artist: str, hyphen: str, name: str):
    try:
        result = 'Artist :' + artist + "Name: " + name
    except Exception:
        await bot.say('Format has to be: Artist - Song')
        return

    await bot.say(result)


with open('config.json', 'r') as f:
    config = json.load(f)

bot_token = config['BOT_TOKEN']

bot.run(bot_token)

