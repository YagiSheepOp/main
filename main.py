import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import os
import random
import asyncio

# ---------------- CONFIG ---------------- #

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True

bot = commands.Bot(
    command_prefix="!gcart ",
    intents=INTENTS,
    help_command=None
)

DATA_FILE = "data.json"

# ---------------- LOAD DATA ---------------- #

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"generators": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

DATA = load_data()

# ---------------- READY ---------------- #

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ---------------- GCART GROUP ---------------- #

@bot.group(invoke_without_command=True)
async def gcart(ctx):
    embed = discord.Embed(
        title="🎁 GCart Generator",
        description="Use `!gcart help` to see commands",
        color=0x2ecc71
    )
    await ctx.send(embed=embed)

# ---------------- HELP ---------------- #

@gcart.command()
async def help(ctx):
    embed = discord.Embed(
        title="📌 GCart Commands",
        color=0x5865F2
    )

    embed.add_field(
        name="👤 User Commands",
        value=(
            "`!gcart gen` – Open generator menu\n"
            "`!gcart stock` – View available stock"
        ),
        inline=False
    )

    embed.add_field(
        name="🛠 Admin Commands",
        value=(
            "`!gcart create <name>`\n"
            "`!gcart add <name> <email> <pass>`\n"
            "`!gcart clear <name>`"
        ),
        inline=False
    )

    await ctx.send(embed=embed)

# ---------------- GEN MENU ---------------- #

class GenView(View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user

    async def interaction_check(self, interaction):
        return interaction.user == self.user

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
    async def free(self, interaction, button):
        await interaction.response.send_message(
            "✅ Free generators available:\n`mcfa`, `nitro_unchecked`",
            ephemeral=True
        )

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
    async def vip(self, interaction, button):
        await interaction.response.send_message(
            "💎 VIP generators require VIP role",
            ephemeral=True
        )

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
    async def booster(self, interaction, button):
        await interaction.response.send_message(
            "🚀 Booster generators require Booster role",
            ephemeral=True
        )

@gcart.command()
async def gen(ctx):
    embed = discord.Embed(
        title="🎁 Select Generator",
        description="Choose a generator type below",
        color=0x2ecc71
    )
    await ctx.send(embed=embed, view=GenView(ctx.author))

# ---------------- STOCK ---------------- #

@gcart.command()
async def stock(ctx):
    data = load_data()
    gens = data.get("generators", {})

    if not gens:
        await ctx.send("❌ No generators available.")
        return

    desc = ""
    for name, gen in gens.items():
        desc += f"**{name}** — `{len(gen['accounts'])}` accounts\n"

    embed = discord.Embed(
        title="📦 Available Stock",
        description=desc,
        color=0x3498db
    )
    await ctx.send(embed=embed)

# ---------------- CREATE GEN ---------------- #

@gcart.command()
@commands.has_permissions(administrator=True)
async def create(ctx, name):
    data = load_data()

    if name in data["generators"]:
        await ctx.send("❌ Generator already exists.")
        return

    data["generators"][name] = {"accounts": []}
    save_data(data)

    await ctx.send(f"✅ Generator `{name}` created.")

# ---------------- ADD ACCOUNT ---------------- #

@gcart.command()
@commands.has_permissions(administrator=True)
async def add(ctx, name, email, password):
    data = load_data()

    if name not in data["generators"]:
        await ctx.send("❌ Generator not found.")
        return

    data["generators"][name]["accounts"].append({
        "email": email,
        "password": password
    })

    save_data(data)
    await ctx.send(f"✅ Account added to `{name}`.")

# ---------------- CLEAR ---------------- #

@gcart.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, name):
    data = load_data()

    if name not in data["generators"]:
        await ctx.send("❌ Generator not found.")
        return

    data["generators"][name]["accounts"] = []
    save_data(data)

    await ctx.send(f"🧹 Cleared `{name}` stock.")

# ---------------- RUN ---------------- #

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN not set")

bot.run(TOKEN)
