import discord
from discord.ext import commands
import json, time, random, os

with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

TOKEN = os.getenv("TOKEN")

STATUS_TEXT = DATA["status_text"]
VIP_ROLE = DATA["roles"]["vip"]
BOOSTER_ROLE = DATA["roles"]["booster"]
LOGS_CH = DATA["channels"]["logs"]
COOLDOWNS = DATA["cooldowns"]

cooldown_cache = {}

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="!gcart ", intents=intents, help_command=None)


# ---------------- READY ----------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


# ---------------- UTIL ----------------
def has_status(member):
    if not member.activities:
        return False
    for a in member.activities:
        if isinstance(a, discord.CustomActivity):
            if a.name and STATUS_TEXT in a.name:
                return True
    return False


def on_cooldown(user_id, key):
    now = time.time()
    last = cooldown_cache.get((user_id, key), 0)
    if now - last < COOLDOWNS[key]:
        return True, int(COOLDOWNS[key] - (now - last))
    cooldown_cache[(user_id, key)] = now
    return False, 0


# ---------------- EMBEDS ----------------
def status_embed():
    return discord.Embed(
        title="❌ Status Required",
        description=(
            "Use This Status:\n"
            f"```{STATUS_TEXT}```\n"
            "<a:animatedarrowgreen:1450811653552607296> "
            "Use This Status to get Access Of Free Gen"
        ),
        color=0xe74c3c
    )


def vip_missing():
    return discord.Embed(
        description=(
            "<a:Warning:1450809908013563918> You Not Have Vip Role\n"
            "<a:animatedarrowgreen:1450811653552607296> "
            "Buy Vip From https://discord.com/channels/1439302910134583580/1447120310963802182"
        ),
        color=0xf1c40f
    )


def booster_missing():
    return discord.Embed(
        description=(
            "<a:Warning:1450809908013563918> You Not Have Booster Role\n"
            "Boost Server to get booster role"
        ),
        color=0x9b59b6
    )


# ---------------- VIEW ----------------
class GenView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user

    async def interaction_check(self, interaction):
        return interaction.user.id == self.user.id

    async def send_acc(self, interaction, key):
        cd, left = on_cooldown(self.user.id, key)
        if cd:
            return await interaction.response.send_message(
                f"⏳ Cooldown: `{left}s`", ephemeral=True
            )

        stock = DATA["stock"][key]
        if not stock:
            return await interaction.response.send_message(
                "❌ No stock available.", ephemeral=True
            )

        acc = random.choice(stock)

        embed = discord.Embed(
            title="🎁 GCart Delivery",
            description=f"```{acc}```",
            color=0x2ecc71
        )

        await self.user.send(embed=embed)
        await interaction.response.send_message(
            "📩 Account sent in DM", ephemeral=True
        )

        ch = bot.get_channel(LOGS_CH)
        if ch:
            await ch.send(f"✅ `{self.user}` used `{key}` gen")

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
    async def free(self, i, _):
        if not has_status(self.user):
            return await i.response.send_message(embed=status_embed(), ephemeral=True)
        await self.send_acc(i, "free")

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
    async def vip(self, i, _):
        if not has_status(self.user):
            return await i.response.send_message(embed=status_embed(), ephemeral=True)
        if not discord.utils.get(self.user.roles, id=VIP_ROLE):
            return await i.response.send_message(embed=vip_missing(), ephemeral=True)
        await self.send_acc(i, "vip")

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
    async def booster(self, i, _):
        if not has_status(self.user):
            return await i.response.send_message(embed=status_embed(), ephemeral=True)
        if not discord.utils.get(self.user.roles, id=BOOSTER_ROLE):
            return await i.response.send_message(embed=booster_missing(), ephemeral=True)
        await self.send_acc(i, "booster")


# ---------------- COMMANDS ----------------
@bot.command()
async def gen(ctx):
    embed = discord.Embed(
        title="🎁 Select Generator",
        description="Choose a generator below",
        color=0x5865F2
    )
    await ctx.send(embed=embed, view=GenView(ctx.author))


@bot.command()
async def help(ctx):
    await ctx.send(
        "**User Commands**\n"
        "`!gcart gen`\n\n"
        "**Admin**\n"
        "`!gcart bulk <type>`"
    )


@bot.command()
@commands.has_permissions(administrator=True)
async def bulk(ctx, gen_type):
    if gen_type not in DATA["stock"]:
        return await ctx.send("❌ Invalid type")

    await ctx.send("📥 Send accounts line by line. Type `done` when finished.")

    def check(m): return m.author == ctx.author

    items = []
    while True:
        msg = await bot.wait_for("message", check=check)
        if msg.content.lower() == "done":
            break
        items.append(msg.content)

    DATA["stock"][gen_type].extend(items)
    with open("data.json", "w") as f:
        json.dump(DATA, f, indent=2)

    await ctx.send(f"✅ Added `{len(items)}` accounts to `{gen_type}`")


# ---------------- RUN ----------------
bot.run(TOKEN)
