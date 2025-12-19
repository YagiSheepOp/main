import discord
from discord.ext import commands
import os
import json

intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!gcart ", intents=intents)

# ---------------- LOAD DATA ---------------- #
with open("data.json", "r") as f:
    DATA = json.load(f)

REQUIRED_STATUS = DATA["required_status"].lower()


# ---------------- STATUS CHECK ---------------- #
def has_required_status(member):
    try:
        if member.activity and member.activity.state:
            text = str(member.activity.state).lower()
            return REQUIRED_STATUS in text
        return False
    except:
        return False


# ---------------- STATUS ERROR EMBED ---------------- #
async def send_status_error(ctx):
    embed = discord.Embed(
        title="❌ Required Status Not Found",
        description=(
            "<a:animatedarrowgreen:1450811653552607296> Use this status to unlock gen access:\n\n"
            "```\n"
            ".gg/CNFyBV5VnG Best Gen & Best Server ✅\n"
            "```"
        ),
        color=0xff0000
    )
    await ctx.reply(embed=embed, mention_author=False)


# ------------------- GEN MENU ------------------- #
class GenMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
    async def free_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🟢 Free Gen section coming soon...",
            ephemeral=True
        )

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
    async def vip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🔵 VIP Gen section coming soon...",
            ephemeral=True
        )

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
    async def booster_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🔴 Booster Gen section coming soon...",
            ephemeral=True
        )


# ---------------- GEN COMMAND ---------------- #
@bot.command()
async def gen(ctx):
    user = ctx.author

    if not has_required_status(user):
        await send_status_error(ctx)
        return

    embed = discord.Embed(
        title="🎁 Select Generator",
        description="Choose category:",
        color=0x00ff99
    )

    await ctx.reply(embed=embed, view=GenMenu())


# ---------------- STOCK ---------------- #
@bot.command()
async def stock(ctx):

    free = DATA["stock"]["free"]
    vip = DATA["stock"]["vip"]
    booster = DATA["stock"]["booster"]

    embed = discord.Embed(
        title="📦 Stock",
        color=0x00ff99
    )

    embed.add_field(
        name="🟢 FREE",
        value="\n".join([f"{k} → {len(v)}" for k, v in free.items()]),
        inline=False
    )

    embed.add_field(
        name="🔵 VIP",
        value="\n".join([f"{k} → {len(v)}" for k, v in vip.items()]),
        inline=False
    )

    embed.add_field(
        name="🔴 BOOSTER",
        value="\n".join([f"{k} → {len(v)}" for k, v in booster.items()]),
        inline=False
    )

    await ctx.reply(embed=embed)


# ---------------- HELP ---------------- #
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📘 GCart Help",
        description="Basic Commands",
        color=0x00ff99
    )
    embed.add_field(
        name="!gcart gen",
        value="Open generator menu",
        inline=False
    )
    embed.add_field(
        name="!gcart stock",
        value="Check stock availability",
        inline=False
    )
    await ctx.reply(embed=embed)


# ---------------- START BOT ---------------- #
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    print("🚨 ERROR: DISCORD_TOKEN missing!")
else:
    bot.run(TOKEN)
