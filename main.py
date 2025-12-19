import discord
from discord.ext import commands
import json, random, time, os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!gcart ", intents=intents, help_command=None)

with open("data.json", "r") as f:
    DATA = json.load(f)

GENS = DATA["generators"]
ROLES = DATA["roles"]
STATUS = DATA["required_status"]
COOLDOWNS = DATA["cooldowns"]

cooldowns = {}


def save_data():
    with open("data.json", "w") as f:
        json.dump(DATA, f, indent=4)


def check_status(user):
    if not hasattr(user, "activity") or not user.activity:
        return False
    if STATUS.lower() not in user.activity.name.lower():
        return False
    return True


async def send_account(interaction, tier, name):
    now = time.time()
    key = (interaction.user.id, tier)

    if key in cooldowns and now - cooldowns[key] < COOLDOWNS[tier]:
        await interaction.response.send_message("⏳ Cooldown active.", ephemeral=True)
        return

    cooldowns[key] = now
    stock = GENS[tier][name]

    if not stock:
        await interaction.response.send_message("❌ No stock.", ephemeral=True)
        return

    acc = stock.pop(0)
    save_data()

    if tier == "booster" and random.randint(1, 100) <= 5:
        vip_role = discord.utils.get(interaction.guild.roles, name=ROLES["vip"])
        if vip_role:
            await interaction.user.add_roles(vip_role)

    embed = discord.Embed(
        title="🎁 GCart Delivery",
        color=0xff4fd8
    )

    embed.description = (
        "# <a:400125purplebook:1447592335012532334> **GCart Delivery** <a:400125purplebook:1447592335012532334>\n\n"
        "<a:Neysi:1447993564079325267> Your Generated Account <a:Neysi:1447993564079325267>\n\n"
        "<a:CoolDoge:1387445675360522240> **Email**\n"
        f"```{acc['email']}```\n"
        "<a:CoolDoge:1387445675360522240> **Password**\n"
        f"```{acc['password']}```\n\n"
        "<a:Warningggg:1433042494471540836> **Must Do Vouch** "
        "<a:Arrow_White:1396104143088783370>\n"
        "https://discord.com/channels/1439302910134583580/1449070993195794545"
    )

    await interaction.user.send(embed=embed)
    await interaction.response.send_message("✅ Check your DM!", ephemeral=True)


class GenSelect(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Free Gen", style=discord.ButtonStyle.success)
    async def free(self, interaction, button):
        if not check_status(interaction.user):
            await interaction.response.send_message(
                "<a:animatedarrowgreen:1450811653552607296> Use This Status to get Access Of Free Gen\n\n"
                "```.gg/CNFyBV5VnG Best Gen & Best Server ✅```",
                ephemeral=True
            )
            return

        menu = FreeCategory()
        await interaction.response.send_message(
            "📦 Select Free Generator",
            view=menu,
            ephemeral=True
        )

    @discord.ui.button(label="VIP Gen", style=discord.ButtonStyle.primary)
    async def vip(self, interaction, button):
        if not check_status(interaction.user):
            await interaction.response.send_message(
                "<a:animatedarrowgreen:1450811653552607296> Use This Status to get Access Of Free Gen\n\n"
                "```.gg/CNFyBV5VnG Best Gen & Best Server ✅```",
                ephemeral=True
            )
            return

        role = discord.utils.get(interaction.guild.roles, name=ROLES["vip"])
        if role not in interaction.user.roles:
            await interaction.response.send_message(
                "<a:Warning:1450809908013563918> **You Not Have VIP Role**\n"
                "<a:animatedarrowgreen:1450811653552607296>Buy VIP From:\n"
                "https://discord.com/channels/1439302910134583580/1447120310963802182",
                ephemeral=True
            )
            return

        menu = VIPCategory()
        await interaction.response.send_message(
            "📦 Select VIP Generator",
            view=menu,
            ephemeral=True
        )

    @discord.ui.button(label="Booster Gen", style=discord.ButtonStyle.danger)
    async def booster(self, interaction, button):
        if not check_status(interaction.user):
            await interaction.response.send_message(
                "<a:animatedarrowgreen:1450811653552607296> Use This Status to get Access Of Free Gen\n\n"
                "```.gg/CNFyBV5VnG Best Gen & Best Server ✅```",
                ephemeral=True
            )
            return

        role = discord.utils.get(interaction.guild.roles, name=ROLES["booster"])
        if role not in interaction.user.roles:
            await interaction.response.send_message(
                "<a:Warning:1450809908013563918> **You Not Have Booster Role**\n"
                "Boost Server to get Booster role",
                ephemeral=True
            )
            return

        menu = BoosterCategory()
        await interaction.response.send_message(
            "📦 Select Booster Generator",
            view=menu,
            ephemeral=True
        )


class FreeCategory(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="MCFA", style=discord.ButtonStyle.secondary)
    async def mcfa(self, i, b):
        await send_account(i, "free", "mcfa")


class VIPCategory(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="MCFA VIP", style=discord.ButtonStyle.secondary)
    async def vip_mcfa(self, i, b):
        await send_account(i, "vip", "mcfa")


class BoosterCategory(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="MCFA+", style=discord.ButtonStyle.secondary)
    async def mcfa_plus(self, i, b):
        await send_account(i, "booster", "mcfa_plus")


@bot.command()
async def gen(ctx):
    view = GenSelect()
    await ctx.reply("🎁 Select Generator", view=view)


@bot.command()
async def stock(ctx):
    msg = "**📦 Stock**\n"

    for tier in GENS:
        msg += f"\n### 🔹 {tier.upper()}\n"
        for gen in GENS[tier]:
            msg += f"- {gen} → {len(GENS[tier][gen])}\n"

    await ctx.reply(msg)


@bot.event
async def on_ready():
    print("Bot ready!")
    bot.add_view(GenSelect())
    bot.add_view(FreeCategory())
    bot.add_view(VIPCategory())
    bot.add_view(BoosterCategory())


bot.run(os.getenv("DISCORD_TOKEN"))
