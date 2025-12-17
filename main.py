import discord
from discord.ext import commands
from discord.ui import View, Button
import json, os, time, random

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!gcart ",
    intents=intents,
    help_command=None
)

DATA_FILE = "data.json"
LOG_FILE = "logs.txt"
COOLDOWNS = {}

# ---------- UTILS ----------

def log(text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.ctime()} | {text}\n")

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def has_status(member, required):
    if not member.activities:
        return False
    for act in member.activities:
        if isinstance(act, discord.CustomActivity):
            return act.name and required in act.name
    return False

def cooldown_ok(user_id, seconds):
    now = time.time()
    last = COOLDOWNS.get(user_id, 0)
    if now - last < seconds:
        return False, int(seconds - (now - last))
    COOLDOWNS[user_id] = now
    return True, 0

# ---------- READY ----------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    log("Bot started")

# ---------- GCART GROUP ----------

@bot.group(invoke_without_command=True)
async def gcart(ctx):
    await ctx.send("❌ Use `!gcart help`")

# ---------- HELP ----------

@gcart.command()
async def help(ctx):
    embed = discord.Embed(title="📘 GCart Help", color=0x5865F2)
    embed.add_field(
        name="User",
        value="`!gcart gen`\n`!gcart stock`",
        inline=False
    )
    embed.add_field(
        name="Admin",
        value="`!gcart adminhelp`",
        inline=False
    )
    await ctx.send(embed=embed)

@gcart.command()
@commands.has_permissions(administrator=True)
async def adminhelp(ctx):
    embed = discord.Embed(title="🛠 Admin Commands", color=0xE74C3C)
    embed.description = (
        "`!gcart add <gen> <email> <pass>`\n"
        "`!gcart bulk <gen>` (upload txt)\n"
        "`!gcart clear <gen>`"
    )
    await ctx.send(embed=embed)

# ---------- STOCK ----------

@gcart.command()
async def stock(ctx):
    data = load_data()
    desc = ""
    for g, info in data["generators"].items():
        desc += f"**{g}** ({info['tier']}) — `{len(info['accounts'])}`\n"
    embed = discord.Embed(title="📦 Stock", description=desc, color=0x2ECC71)
    await ctx.send(embed=embed)

# ---------- GEN BUTTONS ----------

class GenView(View):
    def __init__(self, user):
        super().__init__(timeout=30)
        self.user = user

    async def interaction_check(self, interaction):
        return interaction.user == self.user

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
    async def free(self, interaction, button):
        await handle_gen(interaction, "free")

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
    async def vip(self, interaction, button):
        await handle_gen(interaction, "vip")

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
    async def booster(self, interaction, button):
        await handle_gen(interaction, "booster")

@gcart.command()
async def gen(ctx):
    ok, wait = cooldown_ok(ctx.author.id, load_data()["cooldown_seconds"])
    if not ok:
        return await ctx.send(f"⏳ Cooldown: {wait}s")

    embed = discord.Embed(
        title="🎁 Select Generator",
        description="Choose below",
        color=0x2ECC71
    )
    await ctx.send(embed=embed, view=GenView(ctx.author))

# ---------- GEN HANDLER ----------

async def handle_gen(interaction, tier):
    member = interaction.user
    data = load_data()

    # OWNER BYPASS
    if interaction.guild.owner_id != member.id:
        if not has_status(member, data["required_status"]):
            return await interaction.response.send_message(
                f"<a:animatedarrowgreen:1450811653552607296> Use this status:\n"
                f"```{data['required_status']}```",
                ephemeral=True
            )

    if tier == "vip" and not discord.utils.get(member.roles, name="VIP"):
        return await interaction.response.send_message(
            "⚠️ You do not have VIP role",
            ephemeral=True
        )

    if tier == "booster" and not member.premium_since:
        return await interaction.response.send_message(
            "⚠️ Boost the server to access Booster Gen",
            ephemeral=True
        )

    gens = [
        g for g, info in data["generators"].items()
        if info["tier"] == tier and info["accounts"]
    ]

    if not gens:
        return await interaction.response.send_message(
            "❌ No stock available",
            ephemeral=True
        )

    chosen = random.choice(gens)
    acc = data["generators"][chosen]["accounts"].pop(0)
    save_data(data)

    # VIP 5% LUCK (Booster)
    if tier == "booster" and random.randint(1, 100) <= 5:
        vip_role = discord.utils.get(interaction.guild.roles, name="VIP")
        if vip_role:
            await member.add_roles(vip_role)

    try:
        await member.send(
            f"# <a:400125purplebook:1447592335012532334> **GCart Delivery**\n"
            f"```{acc['email']}:{acc['password']}```"
        )
        await interaction.response.send_message("✅ Check your DM!", ephemeral=True)
        log(f"{member} generated {chosen}")
    except:
        await interaction.response.send_message("❌ DMs closed", ephemeral=True)

# ---------- ADMIN ADD ----------

@gcart.command()
@commands.has_permissions(administrator=True)
async def add(ctx, gen, email, password):
    data = load_data()
    if gen not in data["generators"]:
        return await ctx.send("❌ Generator not found")
    data["generators"][gen]["accounts"].append({
        "email": email,
        "password": password
    })
    save_data(data)
    await ctx.send("✅ Added")

# ---------- BULK ----------

@gcart.command()
@commands.has_permissions(administrator=True)
async def bulk(ctx, gen):
    if not ctx.message.attachments:
        return await ctx.send("❌ Upload a .txt file")

    data = load_data()
    if gen not in data["generators"]:
        return await ctx.send("❌ Generator not found")

    file = ctx.message.attachments[0]
    content = (await file.read()).decode()

    count = 0
    for line in content.splitlines():
        if ":" in line:
            e, p = line.split(":", 1)
            data["generators"][gen]["accounts"].append({
                "email": e,
                "password": p
            })
            count += 1

    save_data(data)
    await ctx.send(f"✅ Added {count} accounts")

# ---------- CLEAR ----------

@gcart.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, gen):
    data = load_data()
    if gen not in data["generators"]:
        return await ctx.send("❌ Generator not found")
    data["generators"][gen]["accounts"] = []
    save_data(data)
    await ctx.send("🧹 Cleared")

# ---------- RUN ----------

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN missing")

bot.run(TOKEN)
