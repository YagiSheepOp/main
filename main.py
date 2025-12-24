import discord
from discord.ext import commands
from discord.ui import View, Button
import json, os, time, random

# ---------- LOAD DATA ----------
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

STOCK = DATA["stock"]
COOLDOWN = DATA["cooldown_seconds"]
VIP_ROLE = DATA["roles"]["vip"]
BOOSTER_ROLE = DATA["roles"]["booster"]

cooldowns = {}

# ---------- BOT ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!gcart ",
    help_command=None,
    intents=intents
)

# ---------- HELP ----------
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📦 GCart Help",
        color=discord.Color.gold()
    )
    embed.add_field(
        name="User Commands",
        value="`!gcart gen`\n`!gcart stock`",
        inline=False
    )
    embed.add_field(
        name="Admin Commands",
        value="`!gcart add <tier> <item> <value>`\n`!gcart bulk <tier> <item>`",
        inline=False
    )
    await ctx.send(embed=embed)

# ---------- STOCK ----------
@bot.command()
async def stock(ctx):
    embed = discord.Embed(title="📦 GCart Stock", color=discord.Color.green())

    for tier in STOCK:
        txt = ""
        for k, v in STOCK[tier].items():
            txt += f"**{k}** → {len(v)}\n"
        embed.add_field(name=tier.upper(), value=txt or "Empty", inline=False)

    await ctx.send(embed=embed)

# ---------- ADMIN CHECK ----------
def is_admin(ctx):
    return ctx.author.guild_permissions.administrator

# ---------- ADD ----------
@bot.command()
async def add(ctx, tier: str, item: str, *, value: str):
    if not is_admin(ctx):
        return await ctx.send("❌ You Not Have Permission")

    STOCK[tier][item].append(value)
    with open("data.json", "w") as f:
        json.dump(DATA, f, indent=2)

    await ctx.send("✅ Added")

# ---------- BULK ----------
@bot.command()
async def bulk(ctx, tier: str, item: str):
    if not is_admin(ctx):
        return await ctx.send("❌ You Not Have Permission")

    await ctx.send("📥 Send lines. Type `done` to finish.")
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

# ---------- GEN VIEW ----------
class GenView(View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user

    async def interaction_check(self, interaction):
        return interaction.user == self.user

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
    async def free(self, interaction, button):
        await generate(interaction, "free")

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
    async def vip(self, interaction, button):
        if VIP_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "⚠️ You Not Have VIP Role", ephemeral=True
            )
        await generate(interaction, "vip")

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
    async def booster(self, interaction, button):
        if BOOSTER_ROLE not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "⚠️ You Not Have Booster Role", ephemeral=True
            )
        await generate(interaction, "booster")

# ---------- GENERATE ----------
async def generate(interaction, tier):
    uid = interaction.user.id
    now = time.time()

    if uid in cooldowns and now - cooldowns[uid] < COOLDOWN:
        return await interaction.response.send_message(
            "⏳ Cooldown active", ephemeral=True
        )

    available = [(k, v) for k, v in STOCK[tier].items() if v]
    if not available:
        return await interaction.response.send_message(
            "❌ No stock available", ephemeral=True
        )

    item, values = random.choice(available)
    result = values.pop(0)
    cooldowns[uid] = now

    with open("data.json", "w") as f:
        json.dump(DATA, f, indent=2)

    embed = discord.Embed(color=discord.Color.yellow())
    embed.description = (
        "# 📦 GCart Delivery\n"
        f"# 🌀 Generated From {tier.upper()} GEN\n\n"
        "**🔑 Item**\n"
        f"```{item}```\n"
        "**📩 Value**\n"
        f"```{result}```"
    )

    await interaction.user.send(embed=embed)
    await interaction.response.send_message("✅ Sent to DM", ephemeral=True)

# ---------- GEN ----------
@bot.command()
async def gen(ctx):
    embed = discord.Embed(
        title="🎁 Select Generator",
        description="Choose a generator below",
        color=discord.Color.blurple()
    )
    await ctx.send(embed=embed, view=GenView(ctx.author))

# ---------- LUCKY DRAW (UI ONLY) ----------
@bot.command()
async def lucky_draw(ctx):
    embed = discord.Embed(
        title="🎉 Lucky Draw",
        description="Click Join to participate!",
        color=discord.Color.orange()
    )
    view = View()

    view.add_item(
        Button(label="Join Lucky Draw", style=discord.ButtonStyle.success)
    )

    await ctx.send(embed=embed, view=view)

# ---------- RUN ----------
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
