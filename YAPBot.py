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

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
def fixtime(time):
    if not is_number(time):
        minutes, seconds = time.split(':')
        time = int(minutes) * 60 + float(seconds)
    time = float(time)
    ticks = time * (200 / 3)
    ticks = round(ticks)
    fixedtime = ticks / (200 / 3)
    return fixedtime


def time_to_mmss(time):
    time = float(time)
    minutes = floor(time / 60)
    seconds = time % 60
    if minutes > 0:
        return f"{minutes}:{seconds:06.3f}"
    else:
        return seconds


@bot.event
async def on_message(message):
    await bot.process_commands(message)


allowedCategories = ['glitchless', 'mango', 'legacy', 'unrestricted', 'inbounds', 'out of bounds', 'isg']
aliases = {'gless': 'glitchless',
           'gl': 'glitchless',
           'inb': 'inbounds',
           'oob': 'out of bounds',
           'unr': 'unrestricted'}

def get_rrs():
    with open('lb.json', 'r') as f:
        board = json.load(f)
        output = {}
        for category in board:
            for user in board[category]:
                output[category] = user
                break
        return output
def submit_internal(user, category, time, data): # For internal use only, inaccessible to users. Assumes sanitized data.
    data[user][category] = time
    with open('lb.json', 'r') as g:
        lb = json.load(g)
        lb[category][user] = time
        lb[category] = dict(sorted(lb[category].items(), key=lambda item: item[1]))
    with open('lb.json', 'w') as g:
        json.dump(lb, g, indent=4)
    return

def autosubmit(user, category, time):
    with open('data.json', 'r') as f:
        data = json.load(f)
        if user not in data:
            data[user] = {}
        for cat in allowedCategories:
            if cat == 'isg' or allowedCategories.index(cat) < allowedCategories.index(category):
                continue
            if cat not in data[user] or data[user][cat] > time:
                submit_internal(user, cat, time, data)
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)
    return
@bot.hybrid_command()
async def submit(ctx, category: str, time: str):
    category = category.lower()
    if category not in allowedCategories:
        if category in aliases:
            category = aliases[category]
        else:
            await ctx.send(f"Invalid category! Allowed categories: {allowedCategories}")
            return
    try:
        fixedtime = fixtime(time)
    except:
        await ctx.send("Invalid time!")
        return
    user = str(ctx.author)
    autosubmit(user,category, fixedtime)
    with open('lb.json', 'r') as g:
        lb = json.load(g)
        placement = list(lb[category].keys()).index(user)
        await ctx.send(
            f"PB of {time} in {category} by {user} added to database successfully! This places at #{placement + 1}, bopping {time_to_mmss(list(lb[category].values())[placement + 1])} by {list(lb[category].keys())[placement + 1]}")
        rrs = get_rrs()
        current_holder = rrs[category]
        current_record = fixtime(lb[category][current_holder])
        achievementpostifn = bot.get_channel(1259110709975842816)
        if fixedtime < current_record:
            await achievementpostifn.send(f"New r3ds server record of {time_to_mmss(time)} in {category} by {user}!. This beats {current_holder}'s previous record of {time_to_mmss(current_record)} by {time_to_mmss(current_record - fixedtime)}.")
    return


@bot.hybrid_command()
async def pf(ctx, user: str):
    output = f"{user}'s PBs:"
    with open('data.json', 'r') as f:
        data = json.load(f)
        try:
            for cat in data[user]:
                output += f"\n {cat}: {time_to_mmss(data[user][cat])}"
        except KeyError:
            await ctx.send("User not found in database! Make sure you spelled their name correctly.")
    await ctx.send(output)
    return


@bot.hybrid_command()
async def lb(ctx, category):
    category = category.lower()
    if category not in allowedCategories:
        if category in aliases:
            category = aliases[category]
        else:
            await ctx.send(f"Invalid category! Allowed categories: {allowedCategories}")
            return
    with open('lb.json', 'r') as f:
        board = json.load(f)
    output = f"Leaderboard for {category}"
    place = 1
    for user in board[category]:
        output += f"\n {place}. {time_to_mmss(board[category][user])} by {user}"
        place = place + 1
    await ctx.send(output)


@bot.hybrid_command()
async def rr(ctx):
    with open('lb.json', 'r') as f:
        board = json.load(f)
        output = get_rrs()
        rrlist = "Current r3ds server records:"
        for cat in output:
            user = output[cat]
            rrlist += f"\n {cat}: {time_to_mmss(board[cat][user])} by {user}"
        await ctx.send(rrlist)
        return


@bot.hybrid_command()
async def listcommands(ctx):
    await ctx.send("""Command list:
    !submit [category] [time] - Submits a new PB
    !pf [user] - Shows profile for a given user
    !lb [category] - Shows leaderboard for a given category
    !rr - Shows current server records""")
