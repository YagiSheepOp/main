import discord
from discord.ext import commands
from discord.ui import View, Button
import json, os, random

# ---------- LOAD DATA ----------
def load_data():
    with open("data.json", "r") as f:
        return json.load(f)

DATA = load_data()
REQUIRED_STATUS = DATA["required_status"]
ROLES = DATA["roles"]

# ---------- BOT ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!gcart ", intents=intents, help_command=None)

# ---------- UTILS ----------
def has_status(member: discord.Member):
    if not member.activities:
        return False
    for act in member.activities:
        if isinstance(act, discord.CustomActivity) and act.name:
            return REQUIRED_STATUS in act.name
    return False

def has_role(member, role_name):
    return any(r.name == role_name for r in member.roles)

def pop_account(section, name):
    data = load_data()
    stock = data["generators"][section][name]
    if not stock:
        return None
    acc = stock.pop(0)
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)
    return acc

# ---------- BUTTON MENUS ----------
class GeneratorMenu(View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user

    async def interaction_check(self, interaction):
        return interaction.user.id == self.user.id

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
    async def free(self, interaction, _):
        await interaction.response.send_message(
            embed=free_embed(), view=FreeMenu(self.user), ephemeral=True
        )

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
    async def vip(self, interaction, _):
        if not has_status(interaction.user):
            await interaction.response.send_message(status_embed(), ephemeral=True)
            return
        if not has_role(interaction.user, ROLES["vip"]):
            await interaction.response.send_message(vip_role_embed(), ephemeral=True)
            return
        await interaction.response.send_message(
            embed=vip_embed(), view=VIPMenu(self.user), ephemeral=True
        )

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
    async def booster(self, interaction, _):
        if not has_status(interaction.user):
            await interaction.response.send_message(status_embed(), ephemeral=True)
            return
        if not has_role(interaction.user, ROLES["booster"]):
            await interaction.response.send_message(booster_role_embed(), ephemeral=True)
            return
        await interaction.response.send_message(
            embed=booster_embed(), view=BoosterMenu(self.user), ephemeral=True
        )

# ---------- SUB MENUS ----------
class FreeMenu(View):
    def __init__(self, user):
        super().__init__()
        self.user = user

    async def interaction_check(self, i): return i.user.id == self.user.id

    @discord.ui.button(label="mcfa")
    async def mcfa(self, i, _): await send_account(i, "free", "mcfa")

    @discord.ui.button(label="nitro_unchecked")
    async def nitro(self, i, _): await send_account(i, "free", "nitro_unchecked")

    @discord.ui.button(label="mcfa_banned")
    async def banned(self, i, _): await send_account(i, "free", "mcfa_banned")

    @discord.ui.button(label="donut_unbanned")
    async def donut(self, i, _): await send_account(i, "free", "donut_unbanned")

class VIPMenu(View):
    def __init__(self, user):
        super().__init__()
        self.user = user

    async def interaction_check(self, i): return i.user.id == self.user.id

    @discord.ui.button(label="mcfa")
    async def mcfa(self, i, _): await send_account(i, "vip", "mcfa")

    @discord.ui.button(label="steam")
    async def steam(self, i, _): await send_account(i, "vip", "steam")

    @discord.ui.button(label="xbox_random")
    async def xbox(self, i, _): await send_account(i, "vip", "xbox_random")

class BoosterMenu(View):
    def __init__(self, user):
        super().__init__()
        self.user = user

    async def interaction_check(self, i): return i.user.id == self.user.id

    @discord.ui.button(label="gta5")
    async def gta(self, i, _): await send_account(i, "booster", "gta5")

    @discord.ui.button(label="gamekey")
    async def key(self, i, _): await send_account(i, "booster", "gamekey")

# ---------- SEND ACCOUNT ----------
async def send_account(interaction, section, name):
    acc = pop_account(section, name)
    if not acc:
        await interaction.response.send_message("❌ No stock.", ephemeral=True)
        return

    # 5% VIP luck in booster
    if section == "booster" and random.randint(1, 100) <= 5:
        role = discord.utils.get(interaction.guild.roles, name=ROLES["vip"])
        if role:
            await interaction.user.add_roles(role)

    await interaction.user.send(
        f"""# <a:400125purplebook:1447592335012532334> **GCart Delivery**
**Type:** `{name}`
```{acc}
<a:Warningggg:1433042494471540836> **Must Do Vouch**
https://discord.com/channels/1439302910134583580/1449070993195794545
"""
    )
    await interaction.response.send_message("✅ Check your DM", ephemeral=True)

# ---------- EMBEDS ----------
def status_embed():
    return discord.Embed(
        description=f"""
<a:animatedarrowgreen:1450811653552607296> Use This Status:
```{}
        color=discord.Color.red()
    )

def vip_role_embed():
    return discord.Embed(
        description="<a:Warning:1450809908013563918> You Not Have VIP Role",
        color=discord.Color.red()
    )

def booster_role_embed():
    return discord.Embed(
        description="<a:Warning:1450809908013563918> You Not Have Booster Role",
        color=discord.Color.red()
    )

def free_embed(): return discord.Embed(title="🟢 Free Generator")
def vip_embed(): return discord.Embed(title="💎 VIP Generator")
def booster_embed(): return discord.Embed(title="🚀 Booster Generator")

# ---------- COMMANDS ----------
@bot.command()
async def gen(ctx):
    await ctx.send(
        embed=discord.Embed(title="🎁 Select Generator"),
        view=GeneratorMenu(ctx.author)
    )

@bot.command()
async def stock(ctx):
    data = load_data()["generators"]
    embed = discord.Embed(title="📦 Stock", color=discord.Color.green())

    embed.add_field(name="🟢 Free", value="\n".join(data["free"].keys()), inline=False)
    embed.add_field(name="💎 VIP", value="\n".join(data["vip"].keys()), inline=False)
    embed.add_field(name="🚀 Booster", value="\n".join(data["booster"].keys()), inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📘 GCart Help")
    embed.add_field(name="User", value="!gcart gen\n!gcart stock")
    await ctx.send(embed=embed)

# ---------- RUN ----------
bot.run(os.getenv("DISCORD_TOKEN"))
