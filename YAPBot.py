import discord
from discord.ext import commands
from math import floor
import json

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user}')
def fixticks(sometime):
    ticks = sometime * (200/3)
    ticks = round(ticks)
    sometime = ticks / (200/3)
    return sometime
def mmss_to_s(time_str):
    minutes, seconds = time_str.split(':')
    time_str =  int(minutes) * 60 + float(seconds)
    time_str = fixticks(time_str)
    return time_str
def time_to_mmss(sometime):
    minutes = floor(sometime / 60)
    seconds = sometime % 60
    return f"{minutes}:{seconds:.3f}"
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

async def on_message(message):
    await bot.process_commands(message)

allowedCategories = ['glitchless', 'inbounds', 'out of bounds', 'legacy', 'unrestricted', 'isg']
aliases = {'gless': 'glitchless',
           'gl': 'glitchless',
           'inb': 'inbounds',
           'oob': 'out of bounds',
           'unr': 'unrestricted'}
@bot.hybrid_command()
async def submitpb(ctx, category: str, time: str):
    if category not in allowedCategories:
        if category in aliases:
            category = aliases[category]
        else:
            await ctx.send(f"Invalid category! Allowed categories: {allowedCategories}")
            return
    if is_number(time):
        time = fixticks(float(time))
    else:
        try:
            time = mmss_to_s(time)
        except:
            await ctx.send("Invalid time!")
            return
    user = str(ctx.author)
    with open('data.json', 'r') as f:
        data = json.load(f)
        if user not in data:
            data[user] = {}
        data[user][category] = time
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)
        await ctx.send(f"PB of {time_to_mmss(time)} in {category} added to database successfully!")
    return

@bot.hybrid_command()
async def pf(ctx, user: str):
    output = f"{user}'s PBs:"
    with open('data.json', 'r') as f:
        data = json.load(f)
        for cat in data[user]:
            output += f"\n {cat}: {time_to_mmss(data[user][cat])}"
    await ctx.send(output)
    return
