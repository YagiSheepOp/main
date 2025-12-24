import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random

# ---------- LOAD DATA ----------
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

TOKEN = os.getenv("TOKEN")

STATUS_TEXT = ".gg/CNFyBV5VnG Best Gen & Best Server ✅"

VIP_ROLE = DATA["roles"]["vip"]
BOOSTER_ROLE = DATA["roles"]["booster"]

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


# ---------- READY ----------
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")


# ---------- STATUS CHECK ----------
def has_status(member: discord.Member):
    if not member.activities:
        return False
    for act in member.activities:
        if isinstance(act, discord.CustomActivity):
            if act.name and STATUS_TEXT in act.name:
                return True
    return False


# ---------- BUTTON VIEW ----------
class GenView(discord.ui.View):
    def __init__(self, user: discord.Member):
        super().__init__(timeout=60)
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.user.id

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
    async def free(self, interaction: discord.Interaction, _):
        if not has_status(interaction.user):
            return await interaction.response.send_message(
                embed=status_embed(), ephemeral=True
            )

        await send_account(interaction, "free")

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
    async def vip(self, interaction: discord.Interaction, _):
        if not has_status(interaction.user):
            return await interaction.response.send_message(
                embed=status_embed(), ephemeral=True
            )

        if not discord.utils.get(interaction.user.roles, id=VIP_ROLE):
            return await interaction.response.send_message(
                embed=vip_missing_embed(), ephemeral=True
            )

        await send_account(interaction, "vip")

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
    async def booster(self, interaction: discord.Interaction, _):
        if not has_status(interaction.user):
            return await interaction.response.send_message(
                embed=status_embed(), ephemeral=True
            )

        if not discord.utils.get(interaction.user.roles, id=BOOSTER_ROLE):
            return await interaction.response.send_message(
                embed=booster_missing_embed(), ephemeral=True
            )

        await send_account(interaction, "booster")


# ---------- EMBEDS ----------
def status_embed():
    return discord.Embed(
        title="❌ Status Required",
        description=(
            "Use This Status:\n"
            f"```{STATUS_TEXT}```"
            "<a:animatedarrowgreen:1450811653552607296> "
            "Use This Status to get Access Of Free Gen"
        ),
        color=0xe74c3c
    )


def vip_missing_embed():
    return discord.Embed(
        description=(
            "<a:Warning:1450809908013563918> You Not Have Vip Role\n"
            "<a:animatedarrowgreen:1450811653552607296>"
            "Buy Vip From https://discord.com/channels/1439302910134583580/1447120310963802182"
        ),
        color=0xf1c40f
    )


def booster_missing_embed():
    return discord.Embed(
        description=(
            "<a:Warning:1450809908013563918> You Not Have Booster Role\n"
            "Boost Server to get booster role"
        ),
        color=0x9b59b6
    )


# ---------- SEND ACCOUNT ----------
async def send_account(interaction, category):
    stock = DATA["stock"].get(category, [])
    if not stock:
        return await interaction.response.send_message(
            "❌ No stock available.", ephemeral=True
        )

    acc = random.choice(stock)
    bonus = ""

    if category == "booster" and random.randint(1, 100) <= 5:
        bonus = "\n🎉 **LUCKY DRAW HIT – VIP ACCESS WON!**"

    embed = discord.Embed(
        title="🎁 GCart Delivery",
        description=f"```{acc}```{bonus}",
        color=0x2ecc71
    )

    await interaction.user.send(embed=embed)
    await interaction.response.send_message(
        "📩 Check your DM", ephemeral=True
    )


# ---------- SLASH COMMAND ----------
@tree.command(name="gcart", description="Open generator")
async def gcart(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎁 Select Generator",
        description="Choose a generator below",
        color=0x5865F2
    )
    await interaction.response.send_message(
        embed=embed,
        view=GenView(interaction.user),
        ephemeral=True
    )


# ---------- RUN ----------
if not TOKEN:
    raise RuntimeError("TOKEN missing")

bot.run(TOKEN)
