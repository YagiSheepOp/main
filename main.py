import discord
from discord.ext import commands
from discord.ui import View, Button
import json, os, random, time

# ---------- LOAD DATA ----------
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

REQUIRED_STATUS = DATA["required_status"]
ROLES = DATA["roles"]
COOLDOWNS = DATA["cooldowns"]
GENS = DATA["generators"]

cooldowns = {}

# ---------- BOT ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!gcart ",
    intents=intents,
    help_command=None
)

# ---------- UTILS ----------
def has_status(member):
    for act in member.activities:
        if isinstance(act, discord.CustomActivity):
            if act.name and REQUIRED_STATUS in act.name:
                return True
    return False

def has_role(member, role_name):
    return any(r.name == role_name for r in member.roles)

def save_data():
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(DATA, f, indent=2)

# ---------- READY ----------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ---------- HELP ----------
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📘 GCart Help", color=0x5865F2)
    embed.add_field(name="User", value="!gcart gen\n!gcart stock", inline=False)
    embed.add_field(
        name="Admin",
        value="!gcart add <tier> <name> <email> <pass>",
        inline=False
    )
    await ctx.send(embed=embed)

# ---------- STOCK ----------
@bot.command()
async def stock(ctx):
    embed = discord.Embed(title="📦 GCart Stock", color=0x2ecc71)

    for tier, items in GENS.items():
        text = ""
        for name, accs in items.items():
            text += f"{name} → {len(accs)}\n"
        embed.add_field(name=tier.upper(), value=text or "Empty", inline=False)

    await ctx.send(embed=embed)

# ---------- SEND ACCOUNT ----------
async def send_account(interaction, tier, name):
    now = time.time()
    key = (interaction.user.id, tier)

    if key in cooldowns and now - cooldowns[key] < COOLDOWNS[tier]:
        await interaction.response.send_message(
            "⏳ Cooldown active, wait a bit.",
            ephemeral=True
        )
        return

    cooldowns[key] = now

    stock = GENS[tier][name]
    if not stock:
        await interaction.response.send_message("❌ No stock.", ephemeral=True)
        return

    acc = stock.pop(0)
    save_data()

    # 5% luck booster → VIP
    if tier == "booster" and random.randint(1, 100) <= 5:
        vip_role = discord.utils.get(
            interaction.guild.roles, name=ROLES["vip"]
        )
        if vip_role:
            await interaction.user.add_roles(vip_role)

    embed = discord.Embed(title="🎁 GCart Delivery", color=0xeb459e)
    embed.add_field(name="Email", value=f"`{acc['email']}`", inline=False)
    embed.add_field(name="Password", value=f"`{acc['password']}`", inline=False)

    await interaction.user.send(embed=embed)
    await interaction.response.send_message(
        "✅ Check your DM!",
        ephemeral=True
    )

# ---------- CATEGORY VIEW ----------
class CategoryView(View):
    def __init__(self, tier, user):
        super().__init__(timeout=30)
        self.tier = tier
        self.user = user

        for name in GENS[tier]:
            self.add_item(CategoryButton(tier, name, user))

class CategoryButton(Button):
    def __init__(self, tier, name, user):
        super().__init__(label=name, style=discord.ButtonStyle.secondary)
        self.tier = tier
        self.name = name
        self.user = user

    async def callback(self, interaction):
        if interaction.user.id != self.user.id:
            return

        if not interaction.user.guild_permissions.administrator:
            if not has_status(interaction.user):
                await interaction.response.send_message(
                    "Use this status:\n```" + REQUIRED_STATUS + "```",
                    ephemeral=True
                )
                return

            if self.tier in ("vip", "booster"):
                role_name = ROLES[self.tier]
                if not has_role(interaction.user, role_name):
                    await interaction.response.send_message(
                        f"You need {role_name} role.",
                        ephemeral=True
                    )
                    return

        await send_account(interaction, self.tier, self.name)

# ---------- MAIN GEN ----------
class GenMenu(View):
    def __init__(self, user):
        super().__init__(timeout=30)
        self.user = user

    async def interaction_check(self, interaction):
        return interaction.user.id == self.user.id

    @discord.ui.button(label="Free", style=discord.ButtonStyle.success)
    async def free(self, interaction, _):
        await interaction.response.send_message(
            "Select Free Generator",
            view=CategoryView("free", interaction.user),
            ephemeral=True
        )

    @discord.ui.button(label="VIP", style=discord.ButtonStyle.primary)
    async def vip(self, interaction, _):
        await interaction.response.send_message(
            "Select VIP Generator",
            view=CategoryView("vip", interaction.user),
            ephemeral=True
        )

    @discord.ui.button(label="Booster", style=discord.ButtonStyle.danger)
    async def booster(self, interaction, _):
        await interaction.response.send_message(
            "Select Booster Generator",
            view=CategoryView("booster", interaction.user),
            ephemeral=True
        )

# ---------- GEN COMMAND ----------
@bot.command()
async def gen(ctx):
    await ctx.send(
        embed=discord.Embed(
            title="🎁 Generator Menu",
            description="Choose your generator tier",
            color=0x5865F2
        ),
        view=GenMenu(ctx.author)
    )

# ---------- ADMIN ADD ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def add(ctx, tier, name, email, password):
    if tier not in GENS or name not in GENS[tier]:
        return await ctx.send("❌ Invalid generator")

    GENS[tier][name].append({
        "email": email,
        "password": password
    })
    save_data()
    await ctx.send("✅ Added")

# ---------- RUN ----------
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN missing")

bot.run(token)
