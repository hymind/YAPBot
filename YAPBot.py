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
    board = json.load(f)
with open('golds.json', 'r') as f:
    golds = json.load(f)
with open('rgolds.json', 'r') as f:
    rg = json.load(f)
with open('gb.json', 'r') as f:
    gboard = json.load(f)

allowedCategories = ("isg", "glitchless", "mango", "legacy", "unrestricted", "inbounds", "out of bounds")
aliases = {
    "gless": "glitchless",
    "gl": "glitchless",
    "inb": "inbounds",
    "oob": "out of bounds",
    "unr": "unrestricted",
    "nosla": "legacy",
    "nsla": "legacy"
}
splits = ('00/01', '02/03', '04/05', '06/07', '08', '09', '10', '11/12', '13', '14', '15', '16', '17', '18', '19', 'e00', 'e01', 'e02')
# helpers (sanitize data before using)
def validatecat(cat):
    cat = cat.lower()
    return aliases.get(cat, cat)
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
def get_rrs():
    holders = {}
    for category in board:
        for user in board[category]:
            holders[category] = user
            break
    return holders
def announce(user, cat, time, place, truetime, message):
    bopped = next((k for k, v in board[cat].items() if v == truetime), None)
    if place < len(board[cat]):
        if truetime is not None:
            if bopped == user:
                message += f", improving on your last pb by {time_to_mmss(truetime - time)}"
            else:
                message += f", bopping {time_to_mmss(truetime)} by {bopped}"
        else:
            message += f"\n This is your first (recorded) run in said category, bopping {time_to_mmss(truetime)} by {bopped}!"
    else:
        message += "(last place)"
    return message
def get_rsob(category):
    rsob = 0
    for split in rg[category]:
        rsob += rg[category][split][1]
    return time_to_mmss(rsob)
@bot.event
async def on_message(message):
    await bot.process_commands(message)
@bot.hybrid_command()
async def listcommands(ctx):
    await ctx.send("""Command list:
        !submit [category] [time] - Submits a new PB
        !pf [user] - Shows profile for a given user
        !lb [category] - Shows leaderboard for a given category
        !rr - Shows current server-wide records
        !whatif [category] [time] - Shows what would happen if you submitted a certain time
        !updategolds - Update your golds for a category
        !viewgolds - View your own golds or those of another user
        !rgolds - View server best split times (similar to cgolds)""")
@bot.hybrid_command()
async def submit(ctx, category: str, time: str):
    global data
    global board
    global gboard
    try:
        category = validatecat(category)
    except (KeyError, ValueError):
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
    try:
        originaltime = data[user][category]
    except KeyError:
        originaltime = None
    for cat in allowedCategories:
        if allowedCategories.index(cat) < allowedCategories.index(category):
            if cat == 'isg' and category != isg:
                continue
            if cat not in data[user] or data[user][cat] > time:
                data[user][category] = fixedtime
                board[category][user] = fixedtime
    rrs = get_rrs()
    current_holder = rrs[category]
    current_record = fixtime(board[category][current_holder])
    if fixedtime < current_record:
        achievementpostifn = bot.get_channel(1259110709975842816)
        await achievementpostifn.send(
            f"New server record of {time_to_mmss(time)} in {category} by {user}!\n"
            f"Previous record by {current_holder}: {time_to_mmss(current_record)}\n"
            f"Beaten by {time_to_mmss(current_record - fixedtime)}."
        )
    with open('data.json', 'w') as f:
        json.dump(data,f,indent=4)
    with open('lb.json', 'w') as f:
        json.dump(board, f,indent=4)
    placement = list(board[category].keys()).index(user) + 1
    await ctx.send(announce(user, category, fixedtime, placement, originaltime,
                            f"PB of {time} in {cat} by {user} added to database successfully! \nThis places at {[placement]}"))
    return
@bot.hybrid_command()
async def pf(ctx, user=None):
    if user == None:
        user = str(ctx.author)
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
    try:
        category = validatecat(category)
    except (KeyError, ValueError):
        await ctx.send(f"Invalid category! Allowed categories: {', '.join(allowedCategories)}")
        return
    output = f"Leaderboard for {category}:"
    for place, user in enumerate(board[category], start=1):
        output += f"\n{place}. {time_to_mmss(board[category][user])} by {user}"
    await ctx.send(output)
@bot.hybrid_command()
async def rr(ctx):
    rrs = get_rrs()
    output = "Current r3ds serer records:"
    for cat, user in rrs.items():
        output += f"\n {cat}: {time_to_mmss(board[cat][user])} by {user}"
    await ctx.send(output)
@bot.hybrid_command()
async def whatif(ctx, category, time):
    try:
        category = validatecat(category)
    except (KeyError, ValueError):
        await ctx.send(f"Invalid category! Allowed categories: {', '.join(allowedCategories)}")
        return
    try:
        fixedtime = fixtime(time)
    except ValueError:
        await ctx.send("Invalid time!")
        return
    user = str(ctx.author)
    placement = 0
    for place in board[category]:
        if board[category][place] < fixedtime:
            continue
        bopped = place
        placement = list(board[category].keys()).index(place) + 1
        break
    message = f"If you got a run of {time} in {category}, it would place at #{placement}"
    try:
        truetime = board[category][bopped]
    except KeyError:
        truetime = None
    await ctx.send(announce(user, category, fixedtime, placement, truetime, message))
@bot.hybrid_command()
async def updategolds(ctx, category):
    global golds
    global rg
    try:
        category = validatecat(category)
    except (KeyError, ValueError):
        await ctx.send(f"Invalid category! Allowed categories: {', '.join(allowedCategories)}")
        return
    user = str(ctx.author)
    sob = None
    if user in golds:
        if category in golds[user]:
            sob = sum(list(golds[user][category].values()))
    await ctx.send("Please copy+paste your golds from LiveSplit")
    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel
    try:
        rawgolds = await bot.wait_for('message', check=check, timeout=727)
    except asyncio.TimeoutError:
        await ctx.send("Nvm fuck this shit I ain't got all day")
        return
    parsedgolds = rawgolds.content.splitlines()
    if len(parsedgolds) != len(splits):
        await ctx.send("Copy your full golds please! Idfk what else could be the issue im ngl")
        return
    goldtable = {}
    for time, chamber in zip(parsedgolds, splits):
        time = fixtime(time)
        goldtable[chamber] = time
    if user not in golds:
        golds[user] = {}
    golds[user][category] = goldtable
    rgolds_beaten = []
    for split in splits:
        if split not in rg[category] or goldtable[split] < rg[category][split][1]:
            rg[category][split] = (user, goldtable[split])
            rgolds_beaten.append(split)
    if rgolds_beaten != []:
        achievementpostifn = bot.get_channel(1259110709975842816)
        await achievementpostifn.send(f"New rgolds in {category} chambers {','.join(rgolds_beaten)} by {user}.\n This brings the rsob down to {get_rsob(category)}")
        with open('rgolds.json', 'w') as f:
            json.dump(rg, f, indent=4)
    with open('golds.json','w') as f:
        json.dump(golds,f,indent=4)
    newsob = sum(list(goldtable.values()))
    if sob is not None:
        await ctx.send(f"SoB improved by {time_to_mmss(sob - newsob)}!")
    return
@bot.hybrid_command()
async def viewgolds(ctx, category, user=None):
    if user == None:
        user = str(ctx.author)
    try:
        category = validatecat(category)
    except (KeyError, ValueError):
        await ctx.send(f"Invalid category! Allowed categories: {', '.join(allowedCategories)}")
        return
    output = f"{user}'s golds for category {category}:"
    try:
        for split in splits:
            output += f"\n**{split}**: {time_to_mmss(golds[user][category][split])}"
        output += f"\n\n**SoB**:{time_to_mmss(sum(list(golds[user][category].values())))}"
        await ctx.send(output)
    except KeyError:
        await ctx.send("No golds listed!")
@bot.hybrid_command()
async def rgolds(ctx, category):
    try:
        category = validatecat(category)
    except (KeyError, ValueError):
        await ctx.send(f"Invalid category! Allowed categories: {', '.join(allowedCategories)}")
        return
    msg = f"Server best split times (rgolds) in category {category}:"
    for split in rg[category]:
        msg += f"\n**{split}**: {time_to_mmss(rg[category][split][1])} by {rg[category][split][0]}"
    msg += f"\n\nSoB: {get_rsob(category)}"
    await ctx.send(msg)
    return
