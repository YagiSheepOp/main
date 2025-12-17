import discord
from discord.ext import commands
import json, os, time, random

# ---------- LOAD ----------
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

STATUS_TEXT = DATA["required_status"]
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

# ---------- READY ----------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ---------- HELP ----------
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📘 GCart Help",
        color=0x5865F2
    )
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
    txt = ""
    for k, v in GENS.items():
        txt += f"**{k}** → {len(v['accounts'])}\n"

    await ctx.send(embed=discord.Embed(
        title="📦 Stock",
        description=txt or "Empty",
        color=0x57F287
    ))

# ---------- STATUS CHECK ----------
def has_required_status(member):
    for act in member.activities:
        if isinstance(act, discord.CustomActivity):
            if STATUS_TEXT in (act.name or ""):
                return True
    return False

# ---------- CATEGORY BUTTONS ----------
class CategoryView(discord.ui.View):
    def __init__(self, tier, user):
        super().__init__(timeout=30)
        self.tier = tier
        self.user = user

        for name, gen in GENS.items():
            if gen["tier"] == tier:
                self.add_item(CategoryButton(name, tier, user))

class CategoryButton(discord.ui.Button):
    def __init__(self, gen_name, tier, user):
        super().__init__(
            label=gen_name,
            style=discord.ButtonStyle.secondary
        )
        self.gen_name = gen_name
        self.tier = tier
        self.user = user

    async def callback(self, interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "❌ This menu is not for you.",
                ephemeral=True
            )

        # OWNER / ADMIN BYPASS
        if not interaction.user.guild_permissions.administrator:

            if not has_required_status(interaction.user):
                await interaction.response.send_message(
                    f"<a:animatedarrowgreen:1450811653552607296> Use this status:\n```{STATUS_TEXT}```",
                    ephemeral=True
                )
                return

            if self.tier in ("vip", "booster"):
                role_name = ROLES[self.tier]
                if not discord.utils.get(interaction.user.roles, name=role_name):
                    msg = (
                        "<a:Warning:1450809908013563918> You Not Have Vip Role\n"
                        "<a:animatedarrowgreen:1450811653552607296> Buy VIP"
                        if self.tier == "vip"
                        else "<a:Warning:1450809908013563918> You Not Have Booster Role\nBoost Server to get Booster"
                    )
                    await interaction.response.send_message(msg, ephemeral=True)
                    return

        # COOLDOWN
        key = (interaction.user.id, self.tier)
        now = time.time()
        cd = COOLDOWNS[self.tier]

        if key in cooldowns and now - cooldowns[key] < cd:
            await interaction.response.send_message(
                f"⏳ Wait `{int(cd - (now - cooldowns[key]))}` sec",
                ephemeral=True
            )
            return

        cooldowns[key] = now

        if not GENS[self.gen_name]["accounts"]:
            await interaction.response.send_message("❌ No stock.", ephemeral=True)
            return

        acc = GENS[self.gen_name]["accounts"].pop(0)

        # 5% BOOSTER → VIP
        if self.tier == "booster" and random.randint(1, 100) <= 5:
            vip = discord.utils.get(interaction.guild.roles, name=ROLES["vip"])
            if vip:
                await interaction.user.add_roles(vip)

        embed = discord.Embed(
            title="🎁 GCart Delivery",
            color=0xEB459E
        )
        embed.add_field(name="Email", value=f"```{acc['email']}```", inline=False)
        embed.add_field(name="Password", value=f"```{acc['password']}```", inline=False)

        await interaction.user.send(embed=embed)
        await interaction.response.send_message("✅ Check your DM!", ephemeral=True)

        with open("data.json", "w") as f:
            json.dump(DATA, f, indent=2)

# ---------- MAIN GEN MENU ----------
class GenTierView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=30)
        self.user = user

    async def interaction_check(self, interaction):
        return interaction.user.id == self.user.id

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
    async def free(self, interaction, _):
        await interaction.response.send_message(
            "Select Free Generator",
            view=CategoryView("free", interaction.user),
            ephemeral=True
        )

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
    async def vip(self, interaction, _):
        await interaction.response.send_message(
            "Select VIP Generator",
            view=CategoryView("vip", interaction.user),
            ephemeral=True
        )

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
    async def booster(self, interaction, _):
        await interaction.response.send_message(
            "Select Booster Generator",
            view=CategoryView("booster", interaction.user),
            ephemeral=True
        )

# ---------- GEN ----------
@bot.command()
async def gen(ctx):
    await ctx.send(
        embed=discord.Embed(title="🎁 Select Generator", color=0x5865F2),
        view=GenTierView(ctx.author),
        delete_after=30
    )

# ---------- ADMIN ADD ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def add(ctx, gen, email, password):
    if gen not in GENS:
        return await ctx.send("❌ Invalid generator")
    GENS[gen]["accounts"].append({"email": email, "password": password})
    with open("data.json", "w") as f:
        json.dump(DATA, f, indent=2)
    await ctx.send("✅ Added")

# ---------- BULK ----------
@bot.command()
@commands.has_permissions(administrator=True)
async def bulk(ctx, gen):
    if not ctx.message.attachments:
        return await ctx.send("❌ Upload txt")

    data = (await ctx.message.attachments[0].read()).decode().splitlines()
    for line in data:
        if ":" in line:
            e, p = line.split(":", 1)
            GENS[gen]["accounts"].append({"email": e, "password": p})

    with open("data.json", "w") as f:
        json.dump(DATA, f, indent=2)

    await ctx.send(f"✅ Bulk added {len(data)}")

# ---------- RUN ----------
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN missing")

bot.run(token)
