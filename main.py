import discord
from discord.ext import commands
import json
import random
import os

# ============================
# CONFIG
# ============================

PREFIX = "!"
STATUS_PHRASE = ".gg/CNFyBV5VnG"      # required phrase
ADMIN_ROLE_NAME = "GCartAdmin"
VIP_ROLE_NAME = "VIP"
BOOSTER_ROLE_NAME = "Booster"

FREE_CHANNELS = ["free-gen"]
VIP_CHANNELS = ["vip-gen"]
BOOSTER_CHANNELS = ["booster-gen"]

DATA_FILE = "data.json"

# ============================
# LOAD DATA
# ============================

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            f.write(json.dumps({"generators": {}}))
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# ============================
# FIXED LISTS YOU REQUESTED
# ============================

# FREE GEN
FREE_LIST = [
    "mcfa",
    "nitro_unchecked",
    "mcfa_banned",
    "hypixel_unbanned"
]

# VIP GEN
VIP_LIST = [
    "xbox",
    "mcfa",
    "mcfa_unbanned",
    "donut_unbanned",
    "jiocinema",
    "crunchyroll"
]

# BOOSTER GEN
BOOST_LIST = [
    "mcfa_changeable",
    "mcfa_password_changeable",
    "jiocinema",
    "steam",
    "gta5",
    "gamekey"
]

# PRE-REGISTER ALL GENERATORS
def ensure_generators():
    for gen in FREE_LIST:
        if gen not in data["generators"]:
            data["generators"][gen] = {"tier": "free", "stock": []}

    for gen in VIP_LIST:
        if gen not in data["generators"]:
            data["generators"][gen] = {"tier": "vip", "stock": []}

    for gen in BOOST_LIST:
        if gen not in data["generators"]:
            data["generators"][gen] = {"tier": "booster", "stock": []}

    save_data(data)

ensure_generators()

# ============================
# BOT SETUP
# ============================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ============================
# CHECKS
# ============================

def has_status(user):
    if user.activity and user.activity.state:
        return STATUS_PHRASE.lower() in user.activity.state.lower()
    return False

def tier_allowed(user, tier):
    if user.guild_permissions.administrator:
        return True

    if tier == "free":
        return True

    if tier == "vip":
        return discord.utils.get(user.roles, name=VIP_ROLE_NAME)

    if tier == "booster":
        return discord.utils.get(user.roles, name=BOOSTER_ROLE_NAME)

    return False

# ============================
# GENERATE CMD
# ============================

@bot.command()
async def gcart(ctx, sub=None, gen=None):
    if sub != "gen" or gen is None:
        return

    if gen not in data["generators"]:
        return await ctx.reply("❌ Invalid generator name.")

    tier = data["generators"][gen]["tier"]

    # status check
    if not has_status(ctx.author) and not ctx.author.guild_permissions.administrator:
        return await ctx.reply(
            f"⚠️ {ctx.author.mention} Please set status to include:\n`{STATUS_PHRASE}`"
        )

    # role/tier check
    if not tier_allowed(ctx.author, tier):
        if tier == "vip":
            return await ctx.reply("⭐ You need **VIP role** to use this generator.")
        if tier == "booster":
            return await ctx.reply("🚀 You need **Booster role** to generate.")
        return

    stock = data["generators"][gen]["stock"]
    if len(stock) == 0:
        return await ctx.reply(f"❌ No stock for `{gen}`")

    acc = random.choice(stock)
    data["generators"][gen]["stock"].remove(acc)
    save_data(data)

    email, password = acc.split(":")

    embed = discord.Embed(
        title="🎁 Your Account is Ready!",
        description="Here are your account details:",
        color=discord.Color.gold()
    )
    embed.add_field(name="Email", value=f"```{email}```", inline=False)
    embed.add_field(name="Password", value=f"```{password}```", inline=False)
    embed.set_footer(text="Powered by GCart Bot")

    await ctx.author.send(embed=embed)
    await ctx.reply(f"✅ {ctx.author.mention} Check your **DMs**!")

# ============================
# ADMIN COMMANDS
# ============================

@bot.command()
@commands.has_permissions(administrator=True)
async def gen(ctx, mode=None, gen=None, *args):
    if mode == "add":
        if gen not in data["generators"]:
            return await ctx.reply("❌ Invalid generator.")

        email = args[0]
        password = args[1]
        combo = f"{email}:{password}"

        data["generators"][gen]["stock"].append(combo)
        save_data(data)
        return await ctx.reply("✅ Added.")

    if mode == "list":
        if gen not in data["generators"]:
            return await ctx.reply("❌ Invalid generator.")

        stock = data["generators"][gen]["stock"]
        msg = "\n".join([f"{i}: {x.split(':')[0]}" for i, x in enumerate(stock)])
        return await ctx.reply(f"**Stock for {gen}:**\n```\n{msg}\n```")

    if mode == "remove":
        if gen not in data["generators"]:
            return await ctx.reply("❌ Invalid generator.")
        idx = int(args[0])
        removed = data["generators"][gen]["stock"].pop(idx)
        save_data(data)
        return await ctx.reply(f"🗑 Removed `{removed}`")

    return await ctx.reply("❌ Invalid syntax.")

# ============================
# BOT START
# ============================

TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
