import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import os

# --------------------------------------------
# LOAD DATA
# --------------------------------------------
with open("data.json", "r") as f:
    DATA = json.load(f)

FREE_STOCK = DATA["stock"]["free"]
VIP_STOCK = DATA["stock"]["vip"]
BOOSTER_STOCK = DATA["stock"]["booster"]

REQUIRED_STATUS = DATA["required_status"]
VIP_ROLE_ID = DATA["roles"]["vip"]
BOOSTER_ROLE_ID = DATA["roles"]["booster"]

TOKEN = os.getenv("DISCORD_TOKEN")

# --------------------------------------------
# BOT SETUP
# --------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix="!gcart ",
    intents=intents,
    help_command=None
)

# --------------------------------------------
# STARTUP
# --------------------------------------------
@bot.event
async def on_ready():
    print(f"Bot online as {bot.user}")

# --------------------------------------------
# HELP COMMAND
# --------------------------------------------
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        color=discord.Color.blue(),
        title="📘 GCart Help"
    )

    embed.add_field(
        name="User Commands",
        value="`!gcart gen` — Generate account\n"
              "`!gcart stock` — View stock"
    )

    embed.add_field(
        name="Admin Commands",
        value="`!gcart add <type> <email> <pass>`\n"
              "`!gcart clear <type>`"
    )

    await ctx.reply(embed=embed)

# --------------------------------------------
# STOCK
# --------------------------------------------
@bot.command()
async def stock(ctx):
    def format_stock(section):
        lines = []
        for key, accounts in section.items():
            lines.append(f"**{key}** → `{len(accounts)}`")
        return "\n".join(lines)

    embed = discord.Embed(
        title="📦 Stock",
        color=discord.Color.orange()
    )

    embed.add_field(name="FREE", value=format_stock(FREE_STOCK), inline=False)
    embed.add_field(name="VIP", value=format_stock(VIP_STOCK), inline=False)
    embed.add_field(name="BOOSTER", value=format_stock(BOOSTER_STOCK), inline=False)

    await ctx.reply(embed=embed)

# --------------------------------------------
# GEN — MAIN MENU
# --------------------------------------------
@bot.command()
async def gen(ctx):

    class GenMenu(View):
        def __init__(self):
            super().__init__(timeout=60)

        @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
        async def free(self, interaction, button):
            await handle_free(interaction)

        @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
        async def vip(self, interaction, button):
            await handle_vip(interaction)

        @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
        async def booster(self, interaction, button):
            await handle_booster(interaction)

    embed = discord.Embed(
        title="🎁 Select Generator",
        color=discord.Color.yellow()
    )

    await ctx.reply(embed=embed, view=GenMenu())

# --------------------------------------------
# STATUS CHECK
# --------------------------------------------
async def check_status(user: discord.Member):
    status_text = str(user.activity) if user.activity else ""
    return REQUIRED_STATUS.lower() in status_text.lower()

# --------------------------------------------
# FREE GEN HANDLER
# --------------------------------------------
async def handle_free(interaction):

    member = interaction.user

    if not await check_status(member):
        embed = discord.Embed(
            title="❌ Status Required",
            description=f"Use This Status:\n```\n{REQUIRED_STATUS}\n```",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # choose category
    gen_type = list(FREE_STOCK.keys())[0]
    accounts = FREE_STOCK[gen_type]

    if len(accounts) == 0:
        await interaction.response.send_message("❌ No stock.", ephemeral=True)
        return

    account = accounts.pop()

    # DM delivery
    dm = await member.create_dm()
    embed = discord.Embed(
        title="🎁 GCart Delivery",
        color=discord.Color.green()
    )
    embed.add_field(name="Email", value=f"```{account['email']}```", inline=False)
    embed.add_field(name="Password", value=f"```{account['password']}```", inline=False)
    await dm.send(embed=embed)

    save_data()

    await interaction.response.send_message("📩 Check your DM!", ephemeral=True)

# --------------------------------------------
# VIP
# --------------------------------------------
async def handle_vip(interaction):

    member = interaction.user
    role = discord.utils.get(member.guild.roles, id=VIP_ROLE_ID)

    if role not in member.roles:
        await interaction.response.send_message("❌ VIP role required.", ephemeral=True)
        return

    for gen_type, accounts in VIP_STOCK.items():
        if len(accounts) > 0:
            acc = accounts.pop()
            dm = await member.create_dm()
            embed = discord.Embed(
                title="🎁 VIP Delivery",
                color=discord.Color.gold()
            )
            embed.add_field(name="Email", value=f"```{acc['email']}```", inline=False)
            embed.add_field(name="Password", value=f"```{acc['password']}```", inline=False)
            await dm.send(embed=embed)
            save_data()
            await interaction.response.send_message("📩 DM sent!", ephemeral=True)
            return

    await interaction.response.send_message("❌ VIP stock empty.", ephemeral=True)

# --------------------------------------------
# BOOSTER
# --------------------------------------------
async def handle_booster(interaction):

    member = interaction.user
    role = discord.utils.get(member.guild.roles, id=BOOSTER_ROLE_ID)

    if role not in member.roles:
        await interaction.response.send_message("❌ Booster role required.", ephemeral=True)
        return

    for gen_type, accounts in BOOSTER_STOCK.items():
        if len(accounts) > 0:
            acc = accounts.pop()
            dm = await member.create_dm()
            embed = discord.Embed(
                title="🎁 Booster Delivery",
                color=discord.Color.purple()
            )
            embed.add_field(name="Email", value=f"```{acc['email']}```", inline=False)
            embed.add_field(name="Password", value=f"```{acc['password']}```", inline=False)
            await dm.send(embed=embed)
            save_data()
            await interaction.response.send_message("📩 DM sent!", ephemeral=True)
            return

    await interaction.response.send_message("❌ Booster stock empty.", ephemeral=True)

# --------------------------------------------
# SAVE DATA
# --------------------------------------------
def save_data():
    with open("data.json", "w") as f:
        json.dump(DATA, f, indent=4)

# --------------------------------------------
# RUN BOT
# --------------------------------------------
bot.run(TOKEN)
