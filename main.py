import discord
from discord.ext import commands
from discord.ui import View, Button
import json, os, time, random

# ================== LOAD DATA ==================
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

STOCK = DATA["stock"]
COOLDOWN = DATA["cooldown_seconds"]
VIP_ROLE = DATA["roles"]["vip"]
BOOSTER_ROLE = DATA["roles"]["booster"]

cooldowns = {}

# ================== BOT SETUP ==================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!gcart ",
    help_command=None,
    intents=intents
)

# ================== HELP ==================
@bot.command()
async def help(ctx):
    e = discord.Embed(
        title="📦 GCart Help",
        color=discord.Color.gold(),
        description="""
**User**
`!gcart gen` – Open generator  
`!gcart stock` – View stock  

**Admin**
`!gcart add <tier> <item>`  
`!gcart bulk <tier> <item>`
"""
    )
    await ctx.send(embed=e)

# ================== STOCK VIEW ==================
@bot.command()
async def stock(ctx):
    e = discord.Embed(title="📦 GCart Stock", color=discord.Color.green())

    for tier in ["free", "vip", "booster"]:
        text = ""
        for k, v in STOCK[tier].items():
            text += f"**{k}** → {len(v)}\n"
        e.add_field(name=tier.upper(), value=text or "Empty", inline=False)

    await ctx.send(embed=e)

# ================== ADMIN CHECK ==================
def is_admin(ctx):
    return ctx.author.guild_permissions.administrator

# ================== ADD SINGLE ==================
@bot.command()
async def add(ctx, tier: str, item: str, *, value: str):
    if not is_admin(ctx):
        return await ctx.send("❌ You Not Have Permission")

    tier = tier.lower()
    item = item.lower()

    STOCK[tier][item].append(value)

    with open("data.json", "w") as f:
        json.dump(DATA, f, indent=2)

    await ctx.send("✅ Added")

# ================== BULK ADD ==================
@bot.command()
async def bulk(ctx, tier: str, item: str):
    if not is_admin(ctx):
        return await ctx.send("❌ You Not Have Permission")

    await ctx.send("📥 Send accounts line by line. Type `done` when finished.")

    lines = []

    while True:
        msg = await bot.wait_for("message", check=lambda m: m.author == ctx.author)
        if msg.content.lower() == "done":
            break
        lines.append(msg.content)

    STOCK[tier][item].extend(lines)

    with open("data.json", "w") as f:
        json.dump(DATA, f, indent=2)

    await ctx.send(f"✅ Added {len(lines)} items")

# ================== GEN BUTTON VIEW ==================
class GenView(View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user

    async def interaction_check(self, interaction):
        return interaction.user == self.user

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
    async def free(self, i, b):
        await handle_gen(i, "free")

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
    async def vip(self, i, b):
        if VIP_ROLE not in [r.id for r in i.user.roles]:
            return await i.response.send_message("⚠️ You Not Have VIP Role", ephemeral=True)
        await handle_gen(i, "vip")

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
    async def booster(self, i, b):
        if BOOSTER_ROLE not in [r.id for r in i.user.roles]:
            return await i.response.send_message("⚠️ You Not Have Booster Role", ephemeral=True)
        await handle_gen(i, "booster")

# ================== GENERATOR ==================
async def handle_gen(interaction, tier):
    uid = interaction.user.id
    now = time.time()

    if uid in cooldowns and now - cooldowns[uid] < COOLDOWN:
        return await interaction.response.send_message("⏳ Cooldown active", ephemeral=True)

    available = [(k, v) for k, v in STOCK[tier].items() if v]
    if not available:
        return await interaction.response.send_message("❌ No stock", ephemeral=True)

    item, values = random.choice(available)
    result = values.pop(0)

    cooldowns[uid] = now

    with open("data.json", "w") as f:
        json.dump(DATA, f, indent=2)

    embed = discord.Embed(
        color=discord.Color.yellow(),
        description=f"""
# 📦 GCart Delivery
# 🌀 Generated From **{tier.upper()} GEN**

**🔑 Item**
```{item}

**📩 Value**
```{}
    )

    await interaction.user.send(embed=embed)
    await interaction.response.send_message("✅ Sent to DM", ephemeral=True)

# ================== GEN COMMAND ==================
@bot.command()
async def gen(ctx):
    e = discord.Embed(
        title="🎁 Select Generator",
        description="Choose a generator below",
        color=discord.Color.blurple()
    )
    await ctx.send(embed=e, view=GenView(ctx.author))

# ================== RUN ==================
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
