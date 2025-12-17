import discord
from discord.ext import commands
import json
import random
import os
import time
import aiohttp

# ================= CONFIG =================
PREFIX = "!"
DATA_FILE = "data.json"

ADMIN_ROLE_NAME = "GCartAdmin"
VIP_ROLE_NAME = "VIP"
BOOSTER_ROLE_NAME = "Booster"

COOLDOWN_SECONDS = 200
last_used = {}

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # optional

# ================= INTENTS =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ================= DATA =================
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({
                "required_status_phrase": ".gg/CNFyBV5VnG",
                "generators": {}
            }, f, indent=2)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)

data = load_data()

# ================= HELPERS =================
def norm(x: str):
    return x.lower().replace(" ", "_")

def is_admin(member):
    return (
        member.guild_permissions.administrator or
        any(r.name == ADMIN_ROLE_NAME for r in member.roles)
    )

def has_role(member, role):
    return any(r.name == role for r in member.roles)

def has_required_status(member):
    required = data.get("required_status_phrase", "").lower()
    for act in member.activities:
        if act.type == discord.ActivityType.custom and act.state:
            if required in act.state.lower():
                return True
    return False

async def webhook_log(text):
    if not WEBHOOK_URL:
        return
    async with aiohttp.ClientSession() as s:
        await s.post(WEBHOOK_URL, json={"content": text})

# ================= DM EMBED =================
def build_dm_message(gen, acc, tier):
    tier_text = {
        "free": "FREE GEN",
        "vip": "VIP GEN",
        "booster": "BOOSTER GEN"
    }.get(tier, "GEN")

    return (
        "# <a:400125purplebook:1447592335012532334> **GCart Dilevery** <a:400125purplebook:1447592335012532334>\n\n"
        "<a:Neysi:1447993564079325267> **Your Account Is Here** <a:Neysi:1447993564079325267>\n\n"
        f"<a:Angry_Ping_Happy:1387445548780486816> **You Generated Account From {tier_text}** "
        "<a:Angry_Ping_Happy:1387445548780486816>\n\n"
        "<a:CoolDoge:1387445675360522240> **Here Is Your Account**\n"
        f"```{acc['email']}```\n\n"
        "<a:CoolDoge:1387445675360522240> **Here Is Your Password**\n"
        f"```{acc['password']}```\n\n"
        "<a:Warningggg:1433042494471540836> **Must Do Vouch**\n"
        "<a:Arrow_White:1396104143088783370> "
        "https://discord.com/channels/1439302910134583580/1449070993195794545"
    )

# ================= COMMANDS =================

@bot.command()
async def help(ctx):
    await ctx.send(
        "```"
        "!gcart gen <generator>\n"
        "!gcart stock\n"
        "!gcart dm @user <msg>\n"
        "!gen add <gen> <email> <password>\n"
        "!gen bulkadd <gen>\n"
        "!gen list <gen>\n"
        "!gen remove <gen> <index>\n"
        "!clearstock <gen>\n"
        "!setstatus <text>\n"
        "```"
    )

# ---------- SET STATUS ----------
@bot.command()
async def setstatus(ctx, *, text):
    if not is_admin(ctx.author):
        return await ctx.send("❌ No permission.")
    data["required_status_phrase"] = text
    save_data(data)
    await ctx.send(f"✅ Status requirement updated:\n`{text}`")

# ---------- GCART GROUP ----------
@bot.group(invoke_without_command=True)
async def gcart(ctx):
    await ctx.send("Use `!help`")

# ---------- DM COMMAND ----------
@gcart.command()
async def dm(ctx, member: discord.Member, *, msg):
    if not is_admin(ctx.author):
        return await ctx.send("❌ No permission.")
    try:
        await member.send(msg)
        await ctx.send("✅ DM sent.")
    except:
        await ctx.send("❌ Cannot DM user.")

# ---------- GENERATE ----------
@gcart.command()
async def gen(ctx, generator):
    gen = norm(generator)

    if gen not in data["generators"]:
        return await ctx.send("❌ Invalid generator.")

    info = data["generators"][gen]
    tier = info["tier"]

    # role check
    if not is_admin(ctx.author):
        if tier == "vip" and not has_role(ctx.author, VIP_ROLE_NAME):
            return await ctx.send("⭐ VIP role required.")
        if tier == "booster" and not has_role(ctx.author, BOOSTER_ROLE_NAME):
            return await ctx.send("🚀 Booster role required.")

    # status check
    if not is_admin(ctx.author) and not has_required_status(ctx.author):
        return await ctx.send(
            f"❌ Set your status to include:\n`{data['required_status_phrase']}`"
        )

    # cooldown
    if not is_admin(ctx.author):
        now = time.time()
        if ctx.author.id in last_used and now - last_used[ctx.author.id] < COOLDOWN_SECONDS:
            return await ctx.send("⏳ Cooldown active.")
        last_used[ctx.author.id] = now

    if not info["accounts"]:
        return await ctx.send("❌ No stock.")

    # remove account (no repeat)
    acc = random.choice(info["accounts"])
    info["accounts"].remove(acc)
    save_data(data)

    dm_text = build_dm_message(gen, acc, tier)

    await ctx.author.send(dm_text)
    await ctx.send("✅ Check your DMs!")

    await webhook_log(
        f"🎁 GEN USED\nUser: {ctx.author}\nGenerator: {gen}\nTier: {tier}"
    )

# ---------- STOCK ----------
@gcart.command()
async def stock(ctx):
    txt = ""
    for g, v in data["generators"].items():
        txt += f"{g} → {len(v['accounts'])}\n"
    await ctx.send(f"```{txt}```")

# ---------- ADMIN GEN GROUP ----------
@bot.group()
async def gen(ctx):
    pass

@gen.command()
async def add(ctx, genname, email, password):
    if not is_admin(ctx.author):
        return
    genname = norm(genname)
    data["generators"][genname]["accounts"].append({
        "email": email,
        "password": password
    })
    save_data(data)
    await ctx.send("✅ Added.")

@gen.command()
async def list(ctx, genname):
    if not is_admin(ctx.author):
        return
    genname = norm(genname)
    accs = data["generators"][genname]["accounts"]
    msg = "\n".join([f"{i}: {a['email']}" for i, a in enumerate(accs)])
    await ctx.send(f"```{msg}```")

@gen.command()
async def remove(ctx, genname, index: int):
    if not is_admin(ctx.author):
        return
    genname = norm(genname)
    data["generators"][genname]["accounts"].pop(index)
    save_data(data)
    await ctx.send("🗑 Removed.")

@gen.command()
async def bulkadd(ctx, genname, *, text=None):
    if not is_admin(ctx.author):
        return
    genname = norm(genname)

    if ctx.message.attachments:
        raw = await ctx.message.attachments[0].read()
        text = raw.decode()

    for line in text.splitlines():
        if ":" in line:
            email, pwd = line.split(":", 1)
            data["generators"][genname]["accounts"].append({
                "email": email.strip(),
                "password": pwd.strip()
            })
    save_data(data)
    await ctx.send("✅ Bulk added.")

# ---------- CLEAR STOCK ----------
@bot.command()
async def clearstock(ctx, genname):
    if not is_admin(ctx.author):
        return
    genname = norm(genname)
    count = len(data["generators"][genname]["accounts"])
    data["generators"][genname]["accounts"].clear()
    save_data(data)
    await ctx.send(f"🧹 Cleared {count} accounts from `{genname}`.")

# ================= START =================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
