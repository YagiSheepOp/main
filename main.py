import discord
from discord.ext import commands
from discord.ui import View, Button
import json, time, random

# ---------- LOAD DATA ----------
with open("data.json", "r") as f:
    DATA = json.load(f)

REQUIRED_STATUS = DATA.get("required_status", "")
COOLDOWN = DATA.get("cooldown_seconds", 60)
ROLES = DATA.get("roles", {})
GENERATORS = DATA.get("generators", {})

cooldowns = {}

# ---------- BOT ----------
intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix="!gcart ",
    intents=intents,
    help_command=None
)

# ---------- UTIL ----------
def is_owner(member: discord.Member):
    if member.guild.owner_id == member.id:
        return True
    return any(r.name.lower() == "owner" for r in member.roles)

def has_role(member, role):
    return any(r.name.lower() == role.lower() for r in member.roles)

def get_status(member):
    for act in member.activities:
        if isinstance(act, discord.CustomActivity) and act.name:
            return act.name
    return ""

def cooldown_ok(uid):
    now = time.time()
    if uid in cooldowns and now - cooldowns[uid] < COOLDOWN:
        return False
    cooldowns[uid] = now
    return True

# ---------- EMBEDS ----------
def status_embed():
    return discord.Embed(
        title="❌ Access Denied",
        description=(
            "<a:animatedarrowgreen:1450811653552607296> **Use This Status to get Access Of Free Gen**\n\n"
            "```"
            ".gg/CNFyBV5VnG Best Gen & Best Server ✅"
            "```"
        ),
        color=discord.Color.red()
    )

def vip_missing():
    return discord.Embed(
        description=(
            "<a:Warning:1450809908013563918> **You Not Have Vip Role**\n"
            "<a:animatedarrowgreen:1450811653552607296> Buy VIP:\n"
            "https://discord.com/channels/1439302910134583580/1447120310963802182"
        ),
        color=discord.Color.orange()
    )

def booster_missing():
    return discord.Embed(
        description=(
            "<a:Warning:1450809908013563918> **You Not Have Booster Role**\n"
            "Boost server to get Booster role."
        ),
        color=discord.Color.orange()
    )

def delivery_embed(gen, email, password, tier):
    return discord.Embed(
        title="# <a:400125purplebook:1447592335012532334> **GCart Delivery** <a:400125purplebook:1447592335012532334>",
        description=(
            f"<a:Neysi:1447993564079325267> Your **{gen.upper()}** Account Is Here\n\n"
            f"<a:CoolDoge:1387445675360522240> **Email**\n```{email}```\n"
            f"<a:CoolDoge:1387445675360522240> **Password**\n```{password}```\n\n"
            f"<a:Angry_Ping_Happy:1387445548780486816> Generated From **{tier.upper()} GEN**\n\n"
            "<a:Warningggg:1433042494471540836> **Must Do Vouch**\n"
            "https://discord.com/channels/1439302910134583580/1449070993195794545"
        ),
        color=discord.Color.green()
    )

# ---------- BUTTON MENU ----------
class GenMenu(View):
    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author

    async def interaction_check(self, interaction):
        return interaction.user.id == self.author.id

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.green)
    async def free(self, interaction, _):
        await show(interaction, "free")

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.blurple)
    async def vip(self, interaction, _):
        await show(interaction, "vip")

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.red)
    async def booster(self, interaction, _):
        await show(interaction, "booster")

# ---------- SHOW GEN ----------
async def show(interaction, tier):
    member = interaction.user

    if not is_owner(member):
        status = get_status(member)
        if REQUIRED_STATUS not in status:
            return await interaction.response.send_message(
                embed=status_embed(), ephemeral=True
            )

        if tier == "vip" and not has_role(member, ROLES["vip"]):
            return await interaction.response.send_message(
                embed=vip_missing(), ephemeral=True
            )

        if tier == "booster" and not has_role(member, ROLES["booster"]):
            return await interaction.response.send_message(
                embed=booster_missing(), ephemeral=True
            )

    view = View(timeout=60)
    for g in GENERATORS[tier]:
        view.add_item(
            Button(
                label=g,
                style=discord.ButtonStyle.secondary,
                custom_id=f"{tier}:{g}"
            )
        )

    await interaction.response.send_message(
        embed=discord.Embed(title=f"{tier.upper()} GENERATORS"),
        view=view,
        ephemeral=True
    )

# ---------- INTERACTION ----------
@bot.event
async def on_interaction(interaction):
    if interaction.type != discord.InteractionType.component:
        return

    cid = interaction.data.get("custom_id", "")
    if ":" not in cid:
        return

    tier, gen = cid.split(":")

    if not cooldown_ok(interaction.user.id):
        return await interaction.response.send_message(
            "⏳ Cooldown active.", ephemeral=True
        )

    stock = GENERATORS[tier][gen]
    if not stock:
        return await interaction.response.send_message(
            "❌ Out of stock.", ephemeral=True
        )

    email, password = stock.pop(0)
    with open("data.json", "w") as f:
        json.dump(DATA, f, indent=2)

    await interaction.user.send(
        embed=delivery_embed(gen, email, password, tier)
    )

    if tier == "booster" and random.randint(1, 100) <= 5:
        role = discord.utils.get(
            interaction.guild.roles, name=ROLES["vip"]
        )
        if role:
            await interaction.user.add_roles(role)

    await interaction.response.send_message(
        "✅ Check your DM!", ephemeral=True
    )

# ---------- COMMANDS ----------
@bot.command()
async def gen(ctx):
    await ctx.send(
        "🎁 **Select Generator**",
        view=GenMenu(ctx.author)
    )

@bot.command()
async def dm(ctx, user: discord.Member, *, msg):
    if not ctx.author.guild_permissions.manage_guild:
        return
    await user.send(msg)
    await ctx.send("✅ DM sent.")

# ---------- RUN ----------
bot.run("YOUR_TOKEN_HERE")
