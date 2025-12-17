import discord
from discord.ext import commands
import json
import os
import random
import time

# ---------- LOAD DATA ----------
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

REQUIRED_STATUS = DATA.get("required_status", "")
ROLES = DATA.get("roles", {})
COOLDOWNS = DATA.get("cooldowns", {})
GENERATORS = DATA.get("generators", {})
VIP_LUCK = DATA.get("vip_luck_percent", 5)

user_cooldowns = {}

# ---------- BOT SETUP ----------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!gcart ", intents=intents)

# ---------- HELP ----------
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="🎁 GCart Commands",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="User Commands",
        value="""
`!gcart gen` – Open generator menu  
`!gcart stock` – View stock
""",
        inline=False
    )
    await ctx.send(embed=embed)

# ---------- STOCK ----------
@bot.command()
async def stock(ctx):
    lines = []
    for name, data in GENERATORS.items():
        lines.append(f"**{name.upper()}** → {len(data['accounts'])} accounts")

    embed = discord.Embed(
        title="📦 Stock",
        description="\n".join(lines) if lines else "No stock",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# ---------- GEN ----------
@bot.command()
async def gen(ctx):
    member = ctx.author

    # Status check (OWNER bypass)
    if not member.guild_permissions.administrator:
        status_ok = False
        for act in member.activities:
            if isinstance(act, discord.CustomActivity):
                if REQUIRED_STATUS in (act.name or ""):
                    status_ok = True

        if not status_ok:
            embed = discord.Embed(
                title="❌ Status Missing",
                description=(
                    "<a:animatedarrowgreen:1450811653552607296> "
                    "Use this status to get access:\n"
                    "```" + REQUIRED_STATUS + "```"
                ),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=15)
            return

    # Cooldown
    now = time.time()
    cd = COOLDOWNS.get("free", 300)
    last = user_cooldowns.get(member.id, 0)

    if now - last < cd:
        await ctx.send(
            f"⏳ Wait `{int(cd - (now - last))}` seconds",
            delete_after=10
        )
        return

    user_cooldowns[member.id] = now

    # Pick generator
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
        await ctx.send("❌ Enable DMs first.", delete_after=10)

    # Save data
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(DATA, f, indent=2)

# ---------- ADD ACCOUNT (ADMIN) ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def add(ctx, gen_name, email, password):
    gen_name = gen_name.lower()
    if gen_name not in GENERATORS:
        await ctx.send("❌ Generator not found")
        return

    GENERATORS[gen_name]["accounts"].append({
        "email": email,
        "password": password
    })

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(DATA, f, indent=2)

    await ctx.send(f"✅ Account added to `{gen_name}`")

# ---------- RUN ----------
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN env variable missing")

bot.run(TOKEN)
