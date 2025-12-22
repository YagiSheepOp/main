import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import random

TOKEN = "YOUR_BOT_TOKEN_HERE"

# -------------------- LOAD DATA --------------------
with open("data.json", "r") as f:
    DATA = json.load(f)

FREE_STOCK = DATA["stock"]["free"]
VIP_STOCK = DATA["stock"]["vip"]
BOOSTER_STOCK = DATA["stock"]["booster"]

STATUS_REQUIRED = DATA["required_status"]

VIP_ROLE_ID = DATA["vip_role_id"]
BOOST_ROLE_ID = DATA["booster_role_id"]

# -------------------- BOT SETUP --------------------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!gcart ", intents=intents, help_command=None)

# -------------------- GENERATOR BUTTON VIEW --------------------
class GenButtons(View):
    def __init__(self, user):
        super().__init__(timeout=30)
        self.user = user

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
    async def free(self, interaction, button):
        if interaction.user != self.user:
            return await interaction.response.send_message("Not for you ❌", ephemeral=True)

        await send_gen_menu(interaction, "free")

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
    async def vip(self, interaction, button):
        if interaction.user != self.user:
            return await interaction.response.send_message("Not for you ❌", ephemeral=True)

        await send_gen_menu(interaction, "vip")

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
    async def booster(self, interaction, button):
        if interaction.user != self.user:
            return await interaction.response.send_message("Not for you ❌", ephemeral=True)

        await send_gen_menu(interaction, "booster")

# -------------------- SEND GEN MENU --------------------
async def send_gen_menu(interaction, tier):
    user = interaction.user

    # STATUS CHECK
    if STATUS_REQUIRED not in (user.activity.name if user.activity else ""):
        embed = discord.Embed(
            title="❌ Status Required",
            description="Use This Status:\n```" + STATUS_REQUIRED + "```",
            color=0xff0000,
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    # ROLE CHECK
    if tier == "vip":
        if not discord.utils.get(user.roles, id=VIP_ROLE_ID):
            return await interaction.response.send_message(
                "> ⚠️ You do not have VIP role.", ephemeral=True
            )
    if tier == "booster":
        if not discord.utils.get(user.roles, id=BOOST_ROLE_ID):
            return await interaction.response.send_message(
                "> ⚠️ You do not have Booster role.", ephemeral=True
            )

    # STOCK LIST
    if tier == "free":
        stock = FREE_STOCK
    elif tier == "vip":
        stock = VIP_STOCK
    else:
        stock = BOOSTER_STOCK

    # NO STOCK CHECK
    all_items = [gen for gen, items in stock.items() if len(items) > 0]

    if not all_items:
        embed = discord.Embed(
            title="❌ No Stock",
            description="No accounts available.",
            color=0xff0000,
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    # SELECT MENU
    class GenSelect(View):
        def __init__(self, tier):
            super().__init__(timeout=30)
            for gen in all_items:
                self.add_item(
                    Button(
                        label=gen,
                        style=discord.ButtonStyle.secondary,
                        custom_id=gen
                    )
                )

        async def interaction_check(self, interaction2):
            if interaction2.user != user:
                await interaction2.response.send_message("Not yours ❌", ephemeral=True)
                return False
            return True

        async def on_timeout(self):
            pass

        @discord.ui.button(label=" ", style=discord.ButtonStyle.grey, disabled=True)
        async def dummy(self, interaction, button):
            pass

        async def callback(self, interaction2):
            gen_id = interaction2.data["custom_id"]
            account = stock[gen_id].pop(0)

            with open("data.json", "w") as f:
                json.dump(DATA, f, indent=4)

            embed = discord.Embed(
                title="🎁 GCart Delivery",
                description=f"Account type: **{gen_id}**\n\n```{account}```",
                color=0x00ff99,
            )
            await user.send(embed=embed)

            await interaction2.response.send_message(
                "> 📬 Delivered in DM!",
                ephemeral=True
            )

    embed = discord.Embed(
        title="🎁 Select Account Type",
        color=0x00ff99
    )
    await interaction.response.send_message(embed=embed, view=GenSelect(tier), ephemeral=True)

# -------------------- MAIN GEN COMMAND --------------------
@bot.command()
async def gen(ctx):
    view = GenButtons(ctx.author)
    embed = discord.Embed(
        title="🎁 Select Generator",
        color=0x00ff99
    )
    await ctx.send(embed=embed, view=view)

# -------------------- STOCK COMMAND --------------------
@bot.command()
async def stock(ctx):

    def count(d):
        return sum(len(v) for v in d.values())

    embed = discord.Embed(
        title="📦 Stock",
        color=0x00ff99
    )

    embed.add_field(name="🎁 Free Vault", value="\n".join([f"{k} ➜ {len(v)}" for k,v in FREE_STOCK.items()]), inline=False)
    embed.add_field(name="💎 VIP Vault", value="\n".join([f"{k} ➜ {len(v)}" for k,v in VIP_STOCK.items()]), inline=False)
    embed.add_field(name="🚀 Booster Vault", value="\n".join([f"{k} ➜ {len(v)}" for k,v in BOOSTER_STOCK.items()]), inline=False)

    await ctx.send(embed=embed)

# -------------------- BOT READY --------------------
@bot.event
async def on_ready():
    print("Bot online as", bot.user)

bot.run(TOKEN)
