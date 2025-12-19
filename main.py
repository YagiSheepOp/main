import discord
from discord.ext import commands
import os
import json
import random

intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!gcart ", intents=intents)
bot.remove_command("help")


# --------------------- LOAD DATA ---------------------
with open("data.json", "r") as f:
    DATA = json.load(f)

REQUIRED_STATUS = DATA["required_status"].lower()
STOCK = DATA["stock"]

FREE_STOCK = STOCK["free"]
VIP_STOCK = STOCK["vip"]
BOOSTER_STOCK = STOCK["booster"]


# ---------------- STATUS CHECK -----------------------
def has_required_status(member):
    try:
        if member.activity and member.activity.state:
            return REQUIRED_STATUS in str(member.activity.state).lower()
        return False
    except:
        return False


async def send_status_error(ctx):
    embed = discord.Embed(
        title="❌ Add Required Status First",
        description=(
            "<a:animatedarrowgreen:1450811653552607296> Use This Status To Get Free Gen Access:\n\n"
            "```\n.gg/CNFyBV5VnG Best Gen & Best Server ✅\n```"
        ),
        color=0xff0000
    )
    await ctx.reply(embed=embed, mention_author=False)


# ---------------- DELIVERY ---------------------------
async def send_account(user, acc_type, account):
    email, password = account.split(":")

    embed = discord.Embed(
        title=f"🎁 {acc_type} Account Delivery",
        color=0x00ff99
    )
    embed.add_field(name="📧 Email", value=f"`{email}`", inline=False)
    embed.add_field(name="🔐 Password", value=f"`{password}`", inline=False)

    await user.send(embed=embed)


# ---------------- STOCK PULL -------------------------
def pull(stock_dict):
    available = [k for k, v in stock_dict.items() if len(v) > 0]
    if not available:
        return None, None

    selected = random.choice(available)
    account = stock_dict[selected].pop(0)

    return selected, account


# ---------------- BUTTON UI --------------------------
class GenMenu(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
    async def free_gen(self, interaction, button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Not your session!", ephemeral=True)
            return

        if not has_required_status(interaction.user):
            await interaction.response.send_message("❌ Add required status!", ephemeral=True)
            return

        acc_type, account = pull(FREE_STOCK)
        if account is None:
            await interaction.response.send_message("❌ No free stock!", ephemeral=True)
        else:
            await send_account(interaction.user, acc_type, account)
            await interaction.response.send_message("📩 Sent in DM!", ephemeral=True)

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
    async def vip_gen(self, interaction, button):
        role = discord.utils.get(interaction.guild.roles, name="VIP")
        if role not in interaction.user.roles:
            await interaction.response.send_message(
                "⚠️ You do not have VIP role!",
                ephemeral=True
            )
            return

        acc_type, account = pull(VIP_STOCK)
        if account is None:
            await interaction.response.send_message("❌ No VIP stock!", ephemeral=True)
        else:
            await send_account(interaction.user, acc_type, account)
            await interaction.response.send_message("📩 Sent in DM!", ephemeral=True)

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
    async def booster_gen(self, interaction, button):
        role = discord.utils.get(interaction.guild.roles, name="Booster")
        if role not in interaction.user.roles:
            await interaction.response.send_message(
                "⚠️ You do not have Booster role!",
                ephemeral=True
            )
            return

        acc_type, account = pull(BOOSTER_STOCK)
        if account is None:
            await interaction.response.send_message("❌ No booster stock!", ephemeral=True)
        else:
            await send_account(interaction.user, acc_type, account)
            await interaction.response.send_message("📩 Sent in DM!", ephemeral=True)


# ---------------- COMMAND: GEN -----------------------
@bot.command()
async def gen(ctx):
    if not has_required_status(ctx.author):
        await send_status_error(ctx)
        return

    embed = discord.Embed(
        title="🎁 Select Generator",
        description="Choose the generator below:",
        color=0x00ff99
    )

    await ctx.reply(embed=embed, view=GenMenu(ctx.author))


# ---------------- COMMAND: STOCK ---------------------
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


# ---------------- COMMAND: HELP ----------------------
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📘 Commands", color=0x00ff99)
    embed.add_field(name="!gcart gen", value="Open generator menu", inline=False)
    embed.add_field(name="!gcart stock", value="View stock", inline=False)
    await ctx.reply(embed=embed)


# ---------------- BOT RUN ----------------------------
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN:
    bot.run(TOKEN)
else:
    print("🚨 ERROR: NO TOKEN FOUND IN RAILWAY")
