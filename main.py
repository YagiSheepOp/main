import discord
from discord.ext import commands
import json
import os
import time

# ---------- LOAD DATA ----------
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

REQUIRED_STATUS = DATA.get("required_status", "")
COOLDOWN_TIME = DATA.get("cooldowns", {}).get("free", 300)
GENERATORS = DATA.get("generators", {})

user_cooldowns = {}

# ---------- BOT SETUP ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!gcart ",
    intents=intents,
    help_command=None   # ✅ FIXES HELP ERROR
)

# ---------- READY ----------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ---------- HELP ----------
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📘 GCart Help",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="User Commands",
        value="""
`!gcart gen` – Generate account  
`!gcart stock` – View stock
""",
        inline=False
    )

    if ctx.author.guild_permissions.administrator:
        embed.add_field(
            name="Admin Commands",
            value="""
`!gcart add <gen> <email> <password>`
""",
            inline=False
        )

    await ctx.send(embed=embed)

# ---------- STOCK ----------
@bot.command()
async def stock(ctx):
    lines = []
    for name, info in GENERATORS.items():
        lines.append(f"**{name}** → {len(info['accounts'])}")

    embed = discord.Embed(
        title="📦 Stock",
        description="\n".join(lines) if lines else "No stock available",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# ---------- GEN ----------
@bot.command()
async def gen(ctx):
    member = ctx.author

    # STATUS CHECK (ADMIN BYPASS)
    if not member.guild_permissions.administrator:
        status_ok = False
        for act in member.activities:
            if isinstance(act, discord.CustomActivity):
                if REQUIRED_STATUS in (act.name or ""):
                    status_ok = True

        if not status_ok:
            embed = discord.Embed(
                title="❌ Status Required",
                description=f"Use this status:\n```{REQUIRED_STATUS}```",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=15)
            return

    # COOLDOWN
    now = time.time()
    last = user_cooldowns.get(member.id, 0)

    if now - last < COOLDOWN_TIME:
        await ctx.send(
            f"⏳ Wait `{int(COOLDOWN_TIME - (now - last))}` seconds",
            delete_after=10
        )
        return

    user_cooldowns[member.id] = now

    # CHECK STOCK
    if "mcfa" not in GENERATORS or not GENERATORS["mcfa"]["accounts"]:
        await ctx.send("❌ No stock available.")
        return

    account = GENERATORS["mcfa"]["accounts"].pop(0)

    embed = discord.Embed(
        title="🎁 GCart Delivery",
        color=discord.Color.purple()
    )
    embed.add_field(name="Email", value=f"```{account['email']}```", inline=False)
    embed.add_field(name="Password", value=f"```{account['password']}```", inline=False)

    try:
        await member.send(embed=embed)
        await ctx.send("✅ Check your DM!", delete_after=10)
    except:
        await ctx.send("❌ Please enable DMs.", delete_after=10)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(DATA, f, indent=2)

# ---------- ADD ACCOUNT (ADMIN) ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def add(ctx, gen, email, password):
    gen = gen.lower()

    if gen not in GENERATORS:
        await ctx.send("❌ Generator not found.")
        return

    GENERATORS[gen]["accounts"].append({
        "email": email,
        "password": password
    })

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(DATA, f, indent=2)

    await ctx.send("✅ Account added.")

# ---------- RUN ----------
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN not set")

bot.run(TOKEN)
