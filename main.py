import discord
from discord.ext import commands
from discord import app_commands
import json, os, time, random

# ---------- LOAD DATA ----------
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

STATUS_TEXT = DATA["required_status"]
ROLES = DATA["roles"]
COOLDOWNS = DATA["cooldowns"]
GENERATORS = DATA["generators"]

user_cooldowns = {}

# ---------- BOT ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!gcart ", intents=intents, help_command=None)

# ---------- READY ----------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# ---------- HELP ----------
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📘 GCart Help", color=0x5865F2)
    embed.add_field(name="User", value="`!gcart gen`\n`!gcart stock`", inline=False)

    if ctx.author.guild_permissions.administrator:
        embed.add_field(
            name="Admin",
            value="`!gcart add <gen> <email> <pass>`\n`!gcart bulk <gen>`",
            inline=False
        )
    await ctx.send(embed=embed)

# ---------- STOCK ----------
@bot.command()
async def stock(ctx):
    text = ""
    for k, v in GENERATORS.items():
        text += f"**{k}** → {len(v['accounts'])}\n"

    await ctx.send(embed=discord.Embed(
        title="📦 Stock",
        description=text or "Empty",
        color=0x57F287
    ))

# ---------- BUTTON VIEW ----------
class GenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    async def interaction_check(self, interaction):
        return True

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
    async def free(self, interaction, button):
        await handle_gen(interaction, "free")

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
    async def vip(self, interaction, button):
        await handle_gen(interaction, "vip")

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
    async def booster(self, interaction, button):
        await handle_gen(interaction, "booster")

# ---------- GEN COMMAND ----------
@bot.command()
async def gen(ctx):
    await ctx.send(
        embed=discord.Embed(title="🎁 Select Generator", color=0x5865F2),
        view=GenView(),
        delete_after=30
    )

# ---------- GEN HANDLER ----------
async def handle_gen(interaction: discord.Interaction, tier: str):
    user = interaction.user

    # OWNER / ADMIN BYPASS
    if not user.guild_permissions.administrator:
        # STATUS CHECK
        has_status = False
        for act in user.activities:
            if isinstance(act, discord.CustomActivity):
                if STATUS_TEXT in (act.name or ""):
                    has_status = True

        if not has_status:
            await interaction.response.send_message(
                f"<a:animatedarrowgreen:1450811653552607296> Use this status:\n```{STATUS_TEXT}```",
                ephemeral=True
            )
            return

    # ROLE CHECK
    if tier in ("vip", "booster"):
        role_name = ROLES[tier]
        if not discord.utils.get(user.roles, name=role_name):
            await interaction.response.send_message(
                f"❌ You need **{role_name}** role.",
                ephemeral=True
            )
            return

    # COOLDOWN
    now = time.time()
    key = (user.id, tier)
    cd = COOLDOWNS[tier]

    if key in user_cooldowns and now - user_cooldowns[key] < cd:
        await interaction.response.send_message(
            f"⏳ Wait `{int(cd - (now - user_cooldowns[key]))}` sec",
            ephemeral=True
        )
        return

    user_cooldowns[key] = now

    # PICK ACCOUNT
    for name, gen in GENERATORS.items():
        if gen["tier"] == tier and gen["accounts"]:
            acc = gen["accounts"].pop(0)

            # 5% BOOSTER → VIP LUCK
            if tier == "booster" and random.randint(1, 100) <= 5:
                vip_role = discord.utils.get(interaction.guild.roles, name=ROLES["vip"])
                if vip_role:
                    await user.add_roles(vip_role)

            embed = discord.Embed(title="🎉 GCart Delivery", color=0xEB459E)
            embed.add_field(name="Email", value=f"```{acc['email']}```", inline=False)
            embed.add_field(name="Password", value=f"```{acc['password']}```", inline=False)

            await user.send(embed=embed)
            await interaction.response.send_message("✅ Check your DM!", ephemeral=True)

            with open("data.json", "w") as f:
                json.dump(DATA, f, indent=2)
            return

    await interaction.response.send_message("❌ No stock.", ephemeral=True)

# ---------- ADD ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def add(ctx, gen, email, password):
    if gen not in GENERATORS:
        await ctx.send("❌ Invalid generator.")
        return
    GENERATORS[gen]["accounts"].append({"email": email, "password": password})
    with open("data.json", "w") as f:
        json.dump(DATA, f, indent=2)
    await ctx.send("✅ Added.")

# ---------- BULK ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def bulk(ctx, gen):
    if not ctx.message.attachments:
        await ctx.send("❌ Upload .txt file")
        return

    file = await ctx.message.attachments[0].read()
    lines = file.decode().splitlines()

    for line in lines:
        if ":" in line:
            e, p = line.split(":", 1)
            GENERATORS[gen]["accounts"].append({"email": e, "password": p})

    with open("data.json", "w") as f:
        json.dump(DATA, f, indent=2)

    await ctx.send(f"✅ Bulk added `{len(lines)}`")

# ---------- RUN ----------
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN missing")

bot.run(token)
