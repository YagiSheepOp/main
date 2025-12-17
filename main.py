import discord
from discord.ext import commands
import os
import json
import random

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# IMPORTANT: disable default help
bot = commands.Bot(
    command_prefix="!gcart ",
    intents=intents,
    help_command=None
)

DATA_FILE = "data.json"

# ---------- UTIL ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"free": {}, "vip": {}, "booster": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

def pop_unique(stock):
    if not stock:
        return None
    item = random.choice(stock)
    stock.remove(item)
    return item

# ---------- READY ----------
@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Game(".gg/CNFyBV5VnG Best Gen Server")
    )
    print(f"Logged in as {bot.user}")

# ---------- HELP ----------
@bot.command()
async def help(ctx):
    await ctx.send(
        "**GCart Commands**\n"
        "`!gcart gen <name>`\n"
        "`!gcart stock`\n"
        "`!gcart add <type> <name> <email> <password>`\n"
        "`!gcart bulk <type> <name>` (upload .txt)\n"
        "`!gcart clear <type> <name>`\n"
        "`!gcart dm @user <msg>`"
    )

# ---------- DM COMMAND ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def dm(ctx, member: discord.Member, *, msg: str):
    try:
        await member.send(msg)
        await ctx.send("✅ DM sent.")
    except:
        await ctx.send("❌ DM failed.")

# ---------- STOCK ----------
@bot.command()
async def stock(ctx):
    text = "**📦 GCart Stock**\n"
    for gtype in data:
        text += f"\n**{gtype.upper()}**\n"
        for k, v in data[gtype].items():
            text += f"- `{k}` → {len(v)}\n"
    await ctx.send(text)

# ---------- ADD ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def add(ctx, gtype, name, email, password):
    gtype = gtype.lower()
    if gtype not in data:
        return await ctx.send("❌ Invalid type")

    data[gtype].setdefault(name, [])
    entry = f"{email}:{password}"

    if entry in data[gtype][name]:
        return await ctx.send("⚠ Already exists")

    data[gtype][name].append(entry)
    save_data(data)
    await ctx.send("✅ Added")

# ---------- BULK ADD ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def bulk(ctx, gtype, name):
    if not ctx.message.attachments:
        return await ctx.send("❌ Upload a .txt file")

    gtype = gtype.lower()
    if gtype not in data:
        return await ctx.send("❌ Invalid type")

    file = ctx.message.attachments[0]
    content = (await file.read()).decode().splitlines()

    data[gtype].setdefault(name, [])
    added = 0

    for line in content:
        if ":" in line and line not in data[gtype][name]:
            data[gtype][name].append(line)
            added += 1

    save_data(data)
    await ctx.send(f"✅ Added {added} accounts")

# ---------- CLEAR ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, gtype, name):
    gtype = gtype.lower()
    if gtype in data and name in data[gtype]:
        data[gtype][name] = []
        save_data(data)
        await ctx.send("🗑 Cleared")
    else:
        await ctx.send("❌ Not found")

# ---------- GEN ----------
@bot.command()
async def gen(ctx, name):
    member = ctx.author

    if ctx.channel.name == "vip-gen" and not discord.utils.get(member.roles, name="VIP"):
        return await ctx.send("❌ VIP role required")

    if ctx.channel.name == "booster-gen" and not discord.utils.get(member.roles, name="Booster"):
        return await ctx.send("❌ Booster role required")

    gtype = "free"
    if ctx.channel.name == "vip-gen":
        gtype = "vip"
    elif ctx.channel.name == "booster-gen":
        gtype = "booster"

    if name not in data[gtype] or not data[gtype][name]:
        return await ctx.send("❌ Out of stock")

    account = pop_unique(data[gtype][name])
    save_data(data)

    email, password = account.split(":", 1)

    embed = (
        "# <a:400125purplebook:1447592335012532334> **GCart Delivery** <a:400125purplebook:1447592335012532334>\n\n"
        f"<a:Neysi:1447993564079325267> Your **{name}** Account Is Here <a:Neysi:1447993564079325267>\n\n"
        f"<a:Angry_Ping_Happy:1387445548780486816> Generated From **{gtype.upper()} GEN** <a:Angry_Ping_Happy:1387445548780486816>\n\n"
        "<a:CoolDoge:1387445675360522240> **Email**\n"
        f"```{email}```\n"
        "<a:CoolDoge:1387445675360522240> **Password**\n"
        f"```{password}```\n\n"
        "<a:Warningggg:1433042494471540836> **Must Do Vouch**\n"
        "<a:Arrow_White:1396104143088783370> https://discord.com/channels/1439302910134583580/1449070993195794545"
    )

    try:
        await member.send(embed)
        await ctx.send("📩 Check your DM")
    except:
        await ctx.send("❌ DM closed")

# ---------- RUN ----------
bot.run(TOKEN)
