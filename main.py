import discord
from discord.ext import commands
import os
import json

# ----------------------------
# LOAD DATA.JSON (Optional safe read)
# ----------------------------
try:
    with open("data.json", "r") as f:
        DATA = json.load(f)
except:
    DATA = {}

# ----------------------------
# DISCORD INTENTS
# ----------------------------
intents = discord.Intents.all()

# ----------------------------
# BOT CLIENT
# ----------------------------
bot = commands.Bot(
    command_prefix="!gcart ",
    intents=intents,
    help_command=None     # Disable default help
)

# ----------------------------
# EVENTS
# ----------------------------
@bot.event
async def on_ready():
    print(f"Bot online as {bot.user}")

# ----------------------------
# COMMAND: HELP
# ----------------------------
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📌 GCart Help",
        description="Working test commands loaded successfully!",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🟢 Commands",
        value="`!gcart help` – Show help menu\n"
              "`!gcart ping` – Check bot status",
        inline=False
    )

    await ctx.send(embed=embed)

# ----------------------------
# COMMAND: PING
# ----------------------------
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! Bot is alive.")

# ----------------------------
# BOT RUN
# ----------------------------
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    print("❌ ERROR: DISCORD_TOKEN not found in Railway variables!")
else:
    bot.run(TOKEN)
