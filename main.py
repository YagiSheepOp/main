import discord
from discord.ext import commands
import json
import os
import random

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!gcart ", intents=intents, help_command=None)

DATA_FILE = "data.json"

# ---------- UTILS ----------

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def is_admin(ctx):
    return ctx.author.guild_permissions.administrator

def has_status(member, phrase):
    if not member.activities:
        return False
    for act in member.activities:
        if isinstance(act, discord.CustomActivity):
            if act.name and phrase in act.name:
                return True
    return False

# ---------- EVENTS ----------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ---------- HELP ----------

@bot.command()
async def help(ctx):
    if is_admin(ctx):
        await ctx.send(
            "**📌 GCart Admin Commands**\n"
            "```"
            "!gcart gen <name>\n"
            "!gcart stock\n"
            "!gcart create <genname> <free/vip/booster>\n"
            "!gcart add <free/vip/booster> <genname> <email> <pass>\n"
            "!gcart bulk <free/vip/booster> <genname> (upload .txt)\n"
            "!gcart clear <free/vip/booster> <genname>\n"
            "!gcart dm @user <message>\n"
            "```"
        )
    else:
        await ctx.send(
            "**📌 GCart Commands**\n"
            "```"
            "!gcart gen <name>\n"
            "!gcart stock\n"
            "```"
        )

# ---------- CREATE GEN ----------

@bot.command()
async def create(ctx, genname: str, tier: str):
    if not is_admin(ctx):
        return

    tier = tier.lower()
    if tier not in ["free", "vip", "booster"]:
        await ctx.send("❌ Invalid tier.")
        return

    data = load_data()
    if genname in data["generators"]:
        await ctx.send("❌ Generator already exists.")
        return

    data["generators"][genname] = {
        "tier": tier,
        "accounts": []
    }

    save_data(data)
    await ctx.send(f"✅ Generator `{genname}` created as `{tier}`.")

# ---------- GEN ----------

@bot.command()
async def gen(ctx, name: str):
    data = load_data()

    if name not in data["generators"]:
        await ctx.send("❌ Invalid generator name.")
        return

    gen = data["generators"][name]

    # Tier checks
    if gen["tier"] == "vip" and not any(r.name.lower() == "vip" for r in ctx.author.roles):
        await ctx.send("❌ VIP role required.")
        return

    if gen["tier"] == "booster" and not ctx.author.premium_since:
        await ctx.send("❌ Booster required.")
        return

    # Status check
    required = data.get("required_status_phrase")
    if required and not has_status(ctx.author, required):
        await ctx.send(f"❌ Set status to: `{required}`")
        return

    if not gen["accounts"]:
        await ctx.send("❌ Out of stock.")
        return

    account = gen["accounts"].pop(0)
    save_data(data)

    await ctx.author.send(
        f"# <a:400125purplebook:1447592335012532334> **GCart Delivery** <a:400125purplebook:1447592335012532334>\n\n"
        f"<a:Neysi:1447993564079325267> Your **{name.upper()}** Account Is Here\n\n"
        f"<a:CoolDoge:1387445675360522240> **Email**\n```{account['email']}```\n"
        f"<a:CoolDoge:1387445675360522240> **Password**\n```{account['password']}```\n\n"
        f"<a:Warningggg:1433042494471540836> **Must Do Vouch** → https://discord.gg/CNFyBV5VnG"
    )

    await ctx.send("✅ Check your DM.")

# ---------- STOCK ----------

@bot.command()
async def stock(ctx):
    data = load_data()
    msg = "**📦 GCart Stock**\n"

    for name, gen in data["generators"].items():
        msg += f"• `{name}` → **{len(gen['accounts'])}**\n"

    await ctx.send(msg)

# ---------- ADD ----------

@bot.command()
async def add(ctx, tier: str, genname: str, email: str, password: str):
    if not is_admin(ctx):
        return

    data = load_data()

    if genname not in data["generators"]:
        await ctx.send("❌ Generator not found.")
        return

    if data["generators"][genname]["tier"] != tier.lower():
        await ctx.send("❌ Tier mismatch.")
        return

    # Prevent duplicates
    for acc in data["generators"][genname]["accounts"]:
        if acc["email"] == email:
            await ctx.send("❌ Duplicate account.")
            return

    data["generators"][genname]["accounts"].append({
        "email": email,
        "password": password
    })

    save_data(data)
    await ctx.send("✅ Account added.")

# ---------- BULK ----------

@bot.command()
async def bulk(ctx, tier: str, genname: str):
    if not is_admin(ctx):
        return

    if not ctx.message.attachments:
        await ctx.send("❌ Upload a .txt file.")
        return

    data = load_data()
    if genname not in data["generators"]:
        await ctx.send("❌ Generator not found.")
        return

    file = await ctx.message.attachments[0].read()
    lines = file.decode().splitlines()

    added = 0
    for line in lines:
        if ":" not in line:
            continue
        email, password = line.split(":", 1)
        data["generators"][genname]["accounts"].append({
            "email": email.strip(),
            "password": password.strip()
        })
        added += 1

    save_data(data)
    await ctx.send(f"✅ Added {added} accounts.")

# ---------- CLEAR ----------

@bot.command()
async def clear(ctx, tier: str, genname: str):
    if not is_admin(ctx):
        return

    data = load_data()
    if genname not in data["generators"]:
        await ctx.send("❌ Generator not found.")
        return

    data["generators"][genname]["accounts"] = []
    save_data(data)

    await ctx.send("🧹 Stock cleared.")

# ---------- DM ----------

@bot.command()
async def dm(ctx, user: discord.Member, *, msg: str):
    if not is_admin(ctx):
        return

    await user.send(msg)
    await ctx.send("✅ DM sent.")

# ---------- RUN ----------

bot.run(TOKEN)
