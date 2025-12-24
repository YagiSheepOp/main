import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import os

# ---------- LOAD CONFIG ----------
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

TOKEN = os.getenv("TOKEN")  # Railway env

VIP_ROLE_ID = DATA["roles"]["vip"]
BOOSTER_ROLE_ID = DATA["roles"]["booster"]

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!gcart ", intents=intents)
tree = bot.tree


# ---------- READY ----------
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot online as {bot.user}")


# ---------- HELP (NO CONFLICT) ----------
@tree.command(name="help", description="GCart Help Menu")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛒 GCart Generator",
        description=(
            "**Free Gen**\n"
            "• mcfa\n• nitro_unchecked\n• donut_unbanned\n\n"
            "**VIP Gen**\n"
            "• steam\n• xbox_random\n• crunchyroll\n\n"
            "**Booster Gen**\n"
            "• nitro\n• gamekey\n• redeem_code\n\n"
            "`/gen` to generate"
        ),
        color=0x2ecc71
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ---------- GEN ----------
@tree.command(name="gen", description="Generate an account")
@app_commands.describe(category="free / vip / booster")
async def gen(interaction: discord.Interaction, category: str):
    user = interaction.user
    guild = interaction.guild

    def has_role(role_id):
        return discord.utils.get(user.roles, id=role_id)

    # ----- ROLE CHECK -----
    if category.lower() == "vip" and not has_role(VIP_ROLE_ID):
        return await interaction.response.send_message(
            "❌ You don't have **VIP role**", ephemeral=True
        )

    if category.lower() == "booster" and not has_role(BOOSTER_ROLE_ID):
        return await interaction.response.send_message(
            "❌ You don't have **Booster role**", ephemeral=True
        )

    stock = DATA["stock"].get(category.lower(), [])
    if not stock:
        return await interaction.response.send_message(
            "⚠️ No stock available", ephemeral=True
        )

    account = random.choice(stock)

    # ----- BOOSTER 5% LUCK -----
    bonus = ""
    if category.lower() == "booster":
        if random.randint(1, 100) <= 5:
            bonus = "\n🎉 **LUCKY BONUS HIT!**"

    embed = discord.Embed(
        title="🎁 Your Generated Account",
        description=f"```{account}```{bonus}",
        color=0x3498db
    )

    await user.send(embed=embed)
    await interaction.response.send_message(
        "📩 **Account sent to your DM**", ephemeral=True
    )


# ---------- RUN ----------
if not TOKEN:
    raise RuntimeError("TOKEN not found in environment variables")

bot.run(TOKEN)
