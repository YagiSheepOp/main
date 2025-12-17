import discord
from discord.ext import commands
import json
import os
import random
import time

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!gcart ", intents=intents, help_command=None)

DATA_FILE = "data.json"

# ---------------- LOAD / SAVE ----------------

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

data = load_data()

# ---------------- COOLDOWN ----------------

cooldowns = {
    "free": 600,
    "vip": 300,
    "booster": 180
}

last_used = {}

def on_cooldown(user_id, tier):
    now = time.time()
    key = f"{user_id}_{tier}"
    if key in last_used and now - last_used[key] < cooldowns[tier]:
        return int(cooldowns[tier] - (now - last_used[key]))
    last_used[key] = now
    return 0

# ---------------- CHECKS ----------------

def has_status(member):
    for a in member.activities:
        if isinstance(a, discord.CustomActivity):
            if a.name and "gg/CNFyBV5VnG" in a.name:
                return True
    return False

def has_role(member, role_name):
    return any(r.name == role_name for r in member.roles)

# ---------------- EMBEDS ----------------

def status_embed():
    return discord.Embed(
        description=(
            "<a:animatedarrowgreen:1450811653552607296> **Use This Status to get Access Of Free Gen**\n\n"
            "```"
            ".gg/CNFyBV5VnG Best Gen & Best Server ✅"
            "```"
        ),
        color=0xff0000
    )

def vip_missing():
    return discord.Embed(
        description=(
            "<a:Warning:1450809908013563918> **You Not Have Vip Role**\n"
            "<a:animatedarrowgreen:1450811653552607296> Buy Vip From:\n"
            "https://discord.com/channels/1439302910134583580/1447120310963802182"
        ),
        color=0xffa500
    )

def booster_missing():
    return discord.Embed(
        description=(
            "<a:Warning:1450809908013563918> **You Not Have Booster Role**\n"
            "Boost Server to get booster role"
        ),
        color=0xff0000
    )

def delivery_embed(name, tier, email, password):
    return discord.Embed(
        title="<a:400125purplebook:1447592335012532334> **GCart Delivery**",
        description=(
            f"<a:Neysi:1447993564079325267> **{name.upper()} ACCOUNT**\n\n"
            f"<a:Angry_Ping_Happy:1387445548780486816> From **{tier.upper()} GEN**\n\n"
            f"**Email**\n```{email}```\n"
            f"**Password**\n```{password}```\n\n"
            "<a:Warningggg:1433042494471540836> **Must Do Vouch**\n"
            "➡ https://discord.gg/CNFyBV5VnG"
        ),
        color=0x9b59b6
    )

# ---------------- GENERATE ----------------

async def generate(interaction, tier, name):
    cd = on_cooldown(interaction.user.id, tier)
    if cd > 0:
        await interaction.response.send_message(
            f"⏳ Cooldown: **{cd}s remaining**",
            ephemeral=True
        )
        return

    stock = data["stock"][tier].get(name, [])
    if not stock:
        await interaction.response.send_message("❌ Out of stock.", ephemeral=True)
        return

    acc = stock.pop(0)
    save_data()

    # 5% VIP LUCKY DRAW
    if tier == "booster" and random.randint(1, 100) <= 5:
        vip_role = discord.utils.get(interaction.guild.roles, name=data["roles"]["vip"])
        if vip_role:
            await interaction.user.add_roles(vip_role)
            await interaction.user.send("🎉 **LUCKY DRAW! You won VIP Role!**")

    try:
        await interaction.user.send(
            embed=delivery_embed(name, tier, acc["email"], acc["password"])
        )
        await interaction.response.send_message("✅ Check your DM!", ephemeral=True)
    except:
        await interaction.response.send_message("❌ DM closed.", ephemeral=True)

# ---------------- BUTTONS ----------------

class MainGen(discord.ui.View):
    @discord.ui.button(label="🆓 Free Gen", style=discord.ButtonStyle.success)
    async def free(self, i, b):
        if not has_status(i.user):
            await i.response.send_message(embed=status_embed(), ephemeral=True)
            return
        await i.response.send_message("Select Free Gen", view=FreeGen(), ephemeral=True)

    @discord.ui.button(label="💎 VIP Gen", style=discord.ButtonStyle.primary)
    async def vip(self, i, b):
        if not has_status(i.user):
            await i.response.send_message(embed=status_embed(), ephemeral=True)
            return
        if not has_role(i.user, data["roles"]["vip"]):
            await i.response.send_message(embed=vip_missing(), ephemeral=True)
            return
        await i.response.send_message("Select VIP Gen", view=VipGen(), ephemeral=True)

    @discord.ui.button(label="🚀 Booster Gen", style=discord.ButtonStyle.danger)
    async def booster(self, i, b):
        if not has_status(i.user):
            await i.response.send_message(embed=status_embed(), ephemeral=True)
            return
        if not has_role(i.user, data["roles"]["booster"]):
            await i.response.send_message(embed=booster_missing(), ephemeral=True)
            return
        await i.response.send_message("Select Booster Gen", view=BoosterGen(), ephemeral=True)

class FreeGen(discord.ui.View):
    @discord.ui.button(label="MCFA", style=discord.ButtonStyle.success)
    async def mcfa(self, i, b):
        await generate(i, "free", "mcfa")

class VipGen(discord.ui.View):
    @discord.ui.button(label="MCFA", style=discord.ButtonStyle.primary)
    async def mcfa(self, i, b):
        await generate(i, "vip", "mcfa")

class BoosterGen(discord.ui.View):
    @discord.ui.button(label="GTA 5", style=discord.ButtonStyle.danger)
    async def gta(self, i, b):
        await generate(i, "booster", "gta5")

# ---------------- COMMANDS ----------------

@bot.command()
async def gen(ctx):
    await ctx.send("🎁 **Select Generator**", view=MainGen())

@bot.command()
@commands.has_permissions(administrator=True)
async def create(ctx, name, tier):
    data["stock"][tier][name] = []
    save_data()
    await ctx.send(f"✅ Generator **{name}** created as **{tier}**")

@bot.command()
@commands.has_permissions(administrator=True)
async def add(ctx, tier, name, email, password):
    data["stock"][tier][name].append({"email": email, "password": password})
    save_data()
    await ctx.send(f"✅ Account added to **{name}**")

@bot.command()
@commands.has_permissions(administrator=True)
async def bulk(ctx, tier, name):
    if not ctx.message.attachments:
        await ctx.send("❌ Upload .txt file")
        return

    file = await ctx.message.attachments[0].read()
    lines = file.decode().splitlines()

    for line in lines:
        if ":" in line:
            e, p = line.split(":", 1)
            data["stock"][tier][name].append({"email": e, "password": p})

    save_data()
    await ctx.send(f"✅ Bulk upload completed ({len(lines)} accounts)")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

bot.run(TOKEN)
