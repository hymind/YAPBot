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

# constants
with open('data.json', 'r') as f:
    data = json.load(f)
with open('lb.json', 'r') as f:
    lb = json.load(f)

allowedCategories = ('isg', 'glitchless', 'mango', 'legacy', 'unrestricted', 'inbounds', 'out of bounds')
seriousCategories = ('glitchless', 'legacy', 'unrestricted', 'inbounds', 'out of bounds')
aliases = {
    'gless': 'glitchless',
    'gl': 'glitchless',
    'inb': 'inbounds',
    'oob': 'out of bounds',
    'unr': 'unrestricted'
}
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

def get_rrs():
    board = load_json('lb.json')
    holders = {}
    for category in board:
        for user in board[category]:
            holders[category] = user
            break
    return holders
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
    global data
    global lb
    category = category.lower()
    if category in aliases:
        category = aliases[category]
    if category not in allowedCategories:
        await ctx.send(f"Invalid category! Allowed categories: {', '.join(allowedCategories)}")
        return
    try:
        fixedtime = fixtime(time)
    except ValueError:
        await ctx.send("Invalid time!")
        return
    user = str(ctx.author)
    if user not in data:
        data[user] = {}
    originaltime = data[user][category]
    for cat in allowedCategories:
        if allowedCategories.index(cat) < allowedCategories.index(category):
            if cat in seriousCategories && category not in seriousCategories:
                continue
            if cat not in data[user] or data[user][cat] > time:
                data[user][category] = fixedtime
                lb[category][user] = fixedtime
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
    with open('data.json', 'w') as f:
        json.dump(f, data)
    with open('lb.json', 'w') as f:
        json.dump(lb, f)
    placement = list(lb[category].keys()).index(user)

    if placement + 1 >= len(lb[category]):
        await ctx.send (f"PB of {time} in {category} by {user} added to database successfully!")
    elif originaltime is Null:
        await ctx.send (f"PB of {time} in {category} by {user} added to database successfully! This is their first (recorded) run in this category!")

    elif list(lb[category].values())[placement + 1] > originaltime:
        await ctx.send (f"PB of {time} in {category} by {user} added to database successfully! This places at #{placement + 1}, bopping {time_to_mmss(list(lb[category].values())[placement + 1])} by {list(lb[category].keys())[placement + 1]}")
    else:
        await ctx.send (f"PB of {time} in {category} by {user} added to database successfully! This places at #{placement + 1}, improving on their last pb by {time_to_mmss(originaltime - fixedtime)}")
    return

@bot.hybrid_command()
async def pf(ctx, user: str):
    await profile(ctx, user)

@bot.hybrid_command()
async def profile(ctx, user: str):
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
async def lb(ctx):
    await leaderboard(ctx)

@bot.hybrid_command()
async def leaderboard(ctx, category):
    category = category.lower
    if category in aliases:
        category = aliases[category]
    if category not in allowedCategories:
        await ctx.send(f"Invalid category! Allowed categories: {', '.join(allowedCategories)}")
        return
    output = f"Leaderboard for {category}:"
    for place, user in enumerate(lb[category], start=1):
        output += f"\n {place}. {time_to_mmss(lb[category][user])} by {user}"
    await ctx.send(output)


@bot.hybrid_command()
async def rainbowroad(ctx):
    await r3dsrecords(ctx)

@bot.hybrid_command()
async def rr(ctx):
    await r3dsrecords()

@bot.hybrid_command()
async def r3dsrecords(ctx):
    r3dsrecords = get_rrs()
    output = "Current r3ds server records:"
    for cat, user in r3dsrecords.items():
        output += f"\n {cat}: {time_to_mmss(lb[cat][user])} by {user}"
    await ctx.send(output)
