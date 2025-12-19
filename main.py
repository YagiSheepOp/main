import discord
from discord.ext import commands
import os
import json
import random

# ----------------------------------------------------
# BOT SETUP
# ----------------------------------------------------
intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!gcart ", intents=intents)
bot.remove_command("help")

# ----------------------------------------------------
# LOAD DATA.JSON
# ----------------------------------------------------
with open("data.json", "r") as f:
    DATA = json.load(f)

REQUIRED_STATUS = DATA["required_status"].lower()

FREE_STOCK = DATA["stock"]["free"]
VIP_STOCK = DATA["stock"]["vip"]
BOOSTER_STOCK = DATA["stock"]["booster"]

# ----------------------------------------------------
# STATUS CHECK FUNCTION
# ----------------------------------------------------
def has_required_status(member):
    try:
        if member.activity and member.activity.state:
            text = str(member.activity.state).lower()
            return REQUIRED_STATUS in text
        return False
    except:
        return False


# ----------------------------------------------------
# ERROR STATUS EMBED
# ----------------------------------------------------
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


# ----------------------------------------------------
# ACCOUNT DELIVERY EMBED
# ----------------------------------------------------
async def send_account(ctx, acc_type, item):
    email, password = item.split(":")

    embed = discord.Embed(
        title=f"🎁 {acc_type} Delivery",
        color=0x00ff99
    )
    embed.add_field(
        name="📧 Email",
        value=f"`{email}`",
        inline=False
    )
    embed.add_field(
        name="🔐 Password",
        value=f"`{password}`",
        inline=False
    )

    await ctx.author.send(embed=embed)
    await ctx.reply("📩 Check your DM!", mention_author=False)


# ----------------------------------------------------
# GEN DELIVERY FUNCTION
# ----------------------------------------------------
def pull_stock(stock_dict):
    valid = [k for k, v in stock_dict.items() if len(v) > 0]
    if not valid:
        return None, None

    choice = random.choice(valid)
    item = stock_dict[choice].pop(0)
    return choice, item


# ----------------------------------------------------
# BUTTON UI MENU
# ----------------------------------------------------
class GenMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
    async def free_button(self, interaction, button):
        if not has_required_status(interaction.user):
            await interaction.response.send_message(
                "❌ You must add status first!", ephemeral=True
            )
            return

        cat, item = pull_stock(FREE_STOCK)
        if item is None:
            await interaction.response.send_message("❌ No stock available.", ephemeral=True)
        else:
            await interaction.response.send_message("📩 Sent to DM!", ephemeral=True)
            await send_account(interaction, cat, item)

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
    async def vip_button(self, interaction, button):
        role = discord.utils.get(interaction.guild.roles, name="VIP")
        if role not in interaction.user.roles:
            await interaction.response.send_message(
                "⚠️ You do not have VIP role!", ephemeral=True
            )
            return

        cat, item = pull_stock(VIP_STOCK)
        if item is None:
            await interaction.response.send_message("❌ No VIP stock.", ephemeral=True)
        else:
            await interaction.response.send_message("📩 Sent to DM!", ephemeral=True)
            await send_account(interaction, cat, item)

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
    async def booster_button(self, interaction, button):
        role = discord.utils.get(interaction.guild.roles, name="Booster")
        if role not in interaction.user.roles:
            await interaction.response.send_message(
                "⚠️ You do not have Booster role!", ephemeral=True
            )
            return

        cat, item = pull_stock(BOOSTER_STOCK)
        if item is None:
            await interaction.response.send_message("❌ No Booster stock.", ephemeral=True)
        else:
            await interaction.response.send_message("📩 Sent to DM!", ephemeral=True)
            await send_account(interaction, cat, item)


# ----------------------------------------------------
# GEN COMMAND
# ----------------------------------------------------
@bot.command()
async def gen(ctx):
    if not has_required_status(ctx.author):
        await send_status_error(ctx)
        return

    embed = discord.Embed(
        title="🎁 Select Generator",
        description="Choose a generator below:",
        color=0x00ff99
    )

    await ctx.reply(embed=embed, view=GenMenu())


# ----------------------------------------------------
# STOCK COMMAND
# ----------------------------------------------------
@bot.command()
async def stock(ctx):
    embed = discord.Embed(title="📦 Stock", color=0x00ff99)

    embed.add_field(
        name="🟢 FREE",
        value="\n".join([f"{k} → {len(v)}" for k, v in FREE_STOCK.items()]),
        inline=False
    )

    embed.add_field(
        name="🔵 VIP",
        value="\n".join([f"{k} → {len(v)}" for k, v in VIP_STOCK.items()]),
        inline=False
    )

    embed.add_field(
        name="🔴 BOOSTER",
        value="\n".join([f"{k} → {len(v)}" for k, v in BOOSTER_STOCK.items()]),
        inline=False
    )

    await ctx.reply(embed=embed)


# ----------------------------------------------------
# HELP COMMAND
# ----------------------------------------------------
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📘 GCart Help",
        description="Basic Commands",
        color=0x00ff99
    )
    embed.add_field(name="!gcart gen", value="Open generator menu", inline=False)
    embed.add_field(name="!gcart stock", value="View stock", inline=False)

    await ctx.reply(embed=embed)


# ----------------------------------------------------
# BOT RUN
# ----------------------------------------------------
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    print("🚨 ERROR: DISCORD_TOKEN NOT SET IN RAILWAY!")
else:
    bot.run(TOKEN)
