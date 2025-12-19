import discord
from discord.ext import commands
from discord.ui import Button, View
import json
import random
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!gcart ", intents=intents)

with open("data.json", "r") as f:
    DATA = json.load(f)

REQUIRED_STATUS = DATA["required_status"]

FREE_STOCK = DATA["stock"]["free"]
VIP_STOCK = DATA["stock"]["vip"]
BOOST_STOCK = DATA["stock"]["booster"]

VIP_ROLE_ID = DATA["roles"]["vip"]
BOOSTER_ROLE_ID = DATA["roles"]["booster"]


# -------------------------------------------------
# STATUS CHECK FIX
# -------------------------------------------------
def has_required_status(user, required_text):
    try:
        if not user.activities:
            return False
        for activity in user.activities:
            if hasattr(activity, "state") and activity.state:
                if required_text.lower() in activity.state.lower():
                    return True
    except:
        pass
    return False


# -------------------------------------------------
# HELP COMMAND
# -------------------------------------------------
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📌 GCart Help",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="User Commands",
        value="`!gcart gen` → Generate an account\n`!gcart stock` → View stock",
        inline=False
    )
    embed.add_field(
        name="Admin Commands",
        value="`!gcart add <gen> <email> <password>`\n`!gcart bulk <gen> <file>`\n`!gcart clear <gen>`",
        inline=False
    )
    await ctx.send(embed=embed)


# -------------------------------------------------
# GEN MENU
# -------------------------------------------------
@bot.command()
async def gen(ctx):

    # Buttons
    free_btn = Button(label="Free Gen", style=discord.ButtonStyle.success)
    vip_btn = Button(label="VIP Gen", style=discord.ButtonStyle.primary)
    boost_btn = Button(label="Booster Gen", style=discord.ButtonStyle.danger)

    async def free_callback(interaction):
        if interaction.user != ctx.author:
            return await interaction.response.send_message(
                "❌ Only the requester can use this.", ephemeral=True
            )

        if not has_required_status(interaction.user, REQUIRED_STATUS):
            embed = discord.Embed(
                title="❌ Status Required",
                description=f"Use This Status:\n```\n{REQUIRED_STATUS}\n```",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if len(FREE_STOCK) == 0:
            return await interaction.response.send_message("❌ No stock available.", ephemeral=True)

        account = FREE_STOCK.pop(0)
        with open("data.json", "w") as f:
            json.dump(DATA, f, indent=4)

        email, password = account.split(":")

        embed = discord.Embed(
            title="🎁 GCart Delivery",
            color=discord.Color.green()
        )
        embed.add_field(name="Email", value=f"`{email}`", inline=False)
        embed.add_field(name="Password", value=f"`{password}`", inline=False)

        await interaction.user.send(embed=embed)
        await interaction.response.send_message("📩 Delivered in DM!", ephemeral=True)

    async def vip_callback(interaction):
        role = interaction.user.get_role(VIP_ROLE_ID)

        if not role:
            return await interaction.response.send_message(
                "❌ You do not have VIP role!", ephemeral=True
            )

        if len(VIP_STOCK) == 0:
            return await interaction.response.send_message("❌ No VIP stock available.", ephemeral=True)

        account = VIP_STOCK.pop(0)
        with open("data.json", "w") as f:
            json.dump(DATA, f, indent=4)

        email, password = account.split(":")

        embed = discord.Embed(
            title="💎 VIP Delivery",
            color=discord.Color.gold()
        )
        embed.add_field(name="Email", value=f"`{email}`", inline=False)
        embed.add_field(name="Password", value=f"`{password}`", inline=False)

        await interaction.user.send(embed=embed)
        await interaction.response.send_message("📩 VIP Delivery in DM!", ephemeral=True)

    async def boost_callback(interaction):
        role = interaction.user.get_role(BOOSTER_ROLE_ID)

        if not role:
            return await interaction.response.send_message(
                "❌ You are not a booster!", ephemeral=True
            )

        if len(BOOST_STOCK) == 0:
            return await interaction.response.send_message("❌ No Booster stock available.", ephemeral=True)

        account = BOOST_STOCK.pop(0)
        with open("data.json", "w") as f:
            json.dump(DATA, f, indent=4)

        email, password = account.split(":")

        embed = discord.Embed(
            title="🚀 Booster Delivery",
            color=discord.Color.purple()
        )
        embed.add_field(name="Email", value=f"`{email}`", inline=False)
        embed.add_field(name="Password", value=f"`{password}`", inline=False)

        await interaction.user.send(embed=embed)
        await interaction.response.send_message("📩 Booster Delivery in DM!", ephemeral=True)

    free_btn.callback = free_callback
    vip_btn.callback = vip_callback
    boost_btn.callback = boost_callback

    view = View()
    view.add_item(free_btn)
    view.add_item(vip_btn)
    view.add_item(boost_btn)

    embed = discord.Embed(
        title="🎁 Select Generator",
        color=discord.Color.blue()
    )

    await ctx.send(embed=embed, view=view)


# -------------------------------------------------
# STOCK CHECK
# -------------------------------------------------
@bot.command()
async def stock(ctx):
    embed = discord.Embed(
        title="📦 Stock",
        color=discord.Color.orange()
    )

    embed.add_field(name="Free", value=len(FREE_STOCK), inline=False)
    embed.add_field(name="VIP", value=len(VIP_STOCK), inline=False)
    embed.add_field(name="Booster", value=len(BOOST_STOCK), inline=False)

    await ctx.send(embed=embed)


# -------------------------------------------------
# BOT READY
# -------------------------------------------------
@bot.event
async def on_ready():
    print(f"Bot online as {bot.user}")


bot.run(os.getenv("DISCORD_TOKEN"))
