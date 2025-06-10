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

# Helper functions. Assume pre-sanitized data
def load_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

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
        return f"{seconds:.3f}"

def normalize_category(cat):
    cat = cat.lower()
    return aliases.get(cat, cat)

def get_rrs():
    board = load_json('lb.json')
    holders = {}
    for category in board:
        for user in board[category]:
            holders[category] = user
            break
    return holders

allowedCategories = ['glitchless', 'mango', 'legacy', 'unrestricted', 'inbounds', 'out of bounds', 'isg']
aliases = {
    'gless': 'glitchless',
    'gl': 'glitchless',
    'inb': 'inbounds',
    'oob': 'out of bounds',
    'unr': 'unrestricted'
}

def submit_internal(user, category, time, data):
    data[user][category] = time
    lb = load_json('lb.json')
    lb[category][user] = time
    lb[category] = dict(sorted(lb[category].items(), key=lambda item: item[1]))
    save_json('lb.json', lb)

def autosubmit(user, category, time):
    data = load_json('data.json')
    if user not in data:
        data[user] = {}
    for cat in allowedCategories:
        if cat == 'isg' or allowedCategories.index(cat) < allowedCategories.index(category):
            continue
        if cat not in data[user] or data[user][cat] > time:
            submit_internal(user, cat, time, data)
    save_json('data.json', data)

@bot.event
async def on_message(message):
    await bot.process_commands(message)

@bot.hybrid_command()
async def listcommands(ctx):
    await ctx.send("""Command list:
    !submit [category] [time] - Submits a new PB
    !pf [user] - Shows profile for a given user
    !lb [category] - Shows leaderboard for a given category
    !wr - Shows current world records""")

@bot.hybrid_command()
async def submit(ctx, category: str, time: str):
    category = normalize_category(category)
    if category not in allowedCategories:
        await ctx.send(f"Invalid category! Allowed categories: {', '.join(allowedCategories)}")
        return
    try:
        fixedtime = fixtime(time)
    except ValueError:
        await ctx.send("Invalid time!")
        return
    user = str(ctx.author)
    if category != 'isg':
        autosubmit(user, category, fixedtime)
    else:
        data = load_json('data.json')
        if user not in data:
            data[user] = {}
        submit_internal(user, category, fixedtime, data)
        save_json('data.json', data)
    lb = load_json('lb.json')
    placement = list(lb[category].keys()).index(user)
    if placement + 1 < len(lb[category]):
        await ctx.send (f"PB of {time} in {category} by {user} added to database successfully! This places at #{placement + 1}, bopping {time_to_mmss(list(lb[category].values())[placement + 1])} by {list(lb[category].keys())[placement + 1]}")
    else:
        await ctx.send (f"PB of {time} in {category} by {user} added to database successfully!")
    rrs = get_rrs()
    current_holder = rrs[category]
    current_record = fixtime(lb[category][current_holder])
    achievement_channel = bot.get_channel(1259110709975842816)
    if fixedtime < current_record:
        await achievement_channel.send(
            f"New server record of {time_to_mmss(time)} in {category} by {user}!\n"
            f"Previous record by {current_holder}: {time_to_mmss(current_record)}\n"
            f"Beaten by {time_to_mmss(current_record - fixedtime)}."
        )


@bot.hybrid_command()
async def pf(ctx, user: str):
    data = load_json('data.json')
    if user not in data:
        await ctx.send("User not found in database! Make sure you spelled their name correctly.")
        return
    if not data[user]:
        await ctx.send(f"{user} has no recorded PBs yet.")
        return
    output = f"{user}'s PBs:"
    for cat, pb_time in data[user].items():
        output += f"\n {cat}: {time_to_mmss(pb_time)}"
    await ctx.send(output)


@bot.hybrid_command()
async def lb(ctx, category):
    category = normalize_category(category)
    if category not in allowedCategories:
        await ctx.send(f"Invalid category! Allowed categories: {', '.join(allowedCategories)}")
        return
    board = load_json('lb.json')
    output = f"Leaderboard for {category}:"
    for place, user in enumerate(board[category], start=1):
        output += f"\n {place}. {time_to_mmss(board[category][user])} by {user}"
    await ctx.send(output)


@bot.hybrid_command()
async def rr(ctx):
    board = load_json('lb.json')
    rrs = get_rrs()
    output = "Current r3ds serer records:"
    for cat, user in rrs.items():
        output += f"\n {cat}: {time_to_mmss(board[cat][user])} by {user}"
    await ctx.send(output)
