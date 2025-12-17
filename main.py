import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import os
import random
import time

# ---------------- LOAD DATA ----------------
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

REQUIRED_STATUS = DATA["required_status"]
ROLES = DATA["roles"]
COOLDOWNS = DATA["cooldowns"]
GENS = DATA["generators"]

# ---------------- BOT SETUP ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!gcart ",
    intents=intents,
    help_command=None
)

last_used = {}

# ---------------- UTILITIES ----------------
def has_status(member: discord.Member):
    if not member.activities:
        return False
    for act in member.activities:
        if isinstance(act, discord.CustomActivity) and act.name:
            if REQUIRED_STATUS in act.name:
                return True
    return False

def cooldown_ok(user_id, tier):
    now = time.time()
    cd = COOLDOWNS[tier]
    last = last_used.get((user_id, tier), 0)
    if now - last < cd:
        return False, int(cd - (now - last))
    last_used[(user_id, tier)] = now
    return True, 0

def is_owner(ctx):
    return ctx.guild and ctx.author == ctx.guild.owner

# ---------------- EVENTS ----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ---------------- HELP ----------------
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="🎁 GCart Commands",
        color=0x2ecc71
    )
    embed.add_field(
        name="User",
        value="""
`!gcart gen`
`!gcart stock`
""",
        inline=False
    )

    if ctx.author.guild_permissions.administrator or is_owner(ctx):
        embed.add_field(
            name="Admin",
            value="""
`!gcart add <tier> <name> <email> <pass>`
`!gcart bulk <tier> <name>`
`!gcart clear <tier> <name>`
`!gcart dm @user <msg>`
""",
            inline=False
        )

    await ctx.send(embed=embed)

# ---------------- GENCARD VIEW ----------------
class GenView(View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx

    async def interaction_check(self, interaction):
        return interaction.user.id == self.ctx.author.id

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
    async def free(self, interaction, button):
        await handle_gen(interaction, "free")

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
    async def vip(self, interaction, button):
        await handle_gen(interaction, "vip")

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
    async def booster(self, interaction, button):
        await handle_gen(interaction, "booster")

# ---------------- GEN HANDLER ----------------
async def handle_gen(interaction, tier):
    member = interaction.user
    guild = interaction.guild

    if not is_owner(interaction) and not has_status(member):
        await interaction.response.send_message(
            embed=discord.Embed(
                description=(
                    "<a:animatedarrowgreen:1450811653552607296> "
                    "**Use This Status to get Access Of Free Gen**\n"
                    f"```{REQUIRED_STATUS}```"
                ),
                color=0xe74c3c
            ),
            ephemeral=True
        )
        return

    if tier == "vip":
        role = discord.utils.get(guild.roles, name=ROLES["vip"])
        if role not in member.roles and not is_owner(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=(
                        "<a:Warning:1450809908013563918> You Not Have VIP Role\n"
                        "<a:animatedarrowgreen:1450811653552607296> Buy VIP"
                    ),
                    color=0xe67e22
                ),
                ephemeral=True
            )
            return

    if tier == "booster":
        role = discord.utils.get(guild.roles, name=ROLES["booster"])
        if role not in member.roles and not is_owner(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=(
                        "<a:Warning:1450809908013563918> You Not Have Booster Role\n"
                        "Boost Server to get Booster Gen"
                    ),
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            return

    ok, wait = cooldown_ok(member.id, tier)
    if not ok:
        await interaction.response.send_message(
            f"⏳ Cooldown active. Wait `{wait}s`",
            ephemeral=True
        )
        return

    stock = GENS[tier]
    name = random.choice(list(stock.keys()))
    if not stock[name]:
        await interaction.response.send_message(
            "❌ Out of stock.",
            ephemeral=True
        )
        return

    acc = stock[name].pop(0)
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(DATA, f, indent=2)

    embed = discord.Embed(
        title="🎁 GCart Delivery",
        color=0x9b59b6
    )
    embed.add_field(name="Account", value=f"```{acc['email']}```", inline=False)
    embed.add_field(name="Password", value=f"```{acc['password']}```", inline=False)

    await member.send(embed=embed)
    await interaction.response.send_message("✅ Check your DM!", ephemeral=True)

# ---------------- COMMANDS ----------------
@bot.command()
async def gen(ctx):
    embed = discord.Embed(
        title="🎁 Select Generator",
        color=0x3498db
    )
    await ctx.send(embed=embed, view=GenView(ctx))

@bot.command()
async def stock(ctx):
    embed = discord.Embed(title="📦 Stock", color=0x2ecc71)
    for tier, items in GENS.items():
        txt = "\n".join(f"{k}: {len(v)}" for k, v in items.items())
        embed.add_field(name=tier.upper(), value=txt or "Empty", inline=False)
    await ctx.send(embed=embed)

# ---------------- ADMIN ----------------
@bot.command()
@commands.has_permissions(administrator=True)
async def add(ctx, tier, name, email, password):
    GENS[tier][name].append({"email": email, "password": password})
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(DATA, f, indent=2)
    await ctx.send("✅ Added")

@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, tier, name):
    GENS[tier][name] = []
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(DATA, f, indent=2)
    await ctx.send("🧹 Cleared")

@bot.command()
@commands.has_permissions(administrator=True)
async def dm(ctx, user: discord.Member, *, msg):
    await user.send(msg)
    await ctx.send("📨 DM Sent")

# ---------------- RUN ----------------
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN env not set")

bot.run(TOKEN)
