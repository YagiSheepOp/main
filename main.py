import discord
from discord.ext import commands
import json
import os

TOKEN = os.getenv("TOKEN")  # Railway env variable

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(
    command_prefix="!gcart ",
    intents=intents,
    help_command=None
)

DATA_FILE = "data.json"


# ---------------- DATA ----------------

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


data = load_data()


# ---------------- UTILS ----------------

def has_required_status(member):
    if not member.activities:
        return False
    for act in member.activities:
        if isinstance(act, discord.CustomActivity):
            if act.name and data["required_status"] in act.name:
                return True
    return False


def has_role(member, role_name):
    return any(r.name == role_name for r in member.roles)


def build_account_embed(gen_name, tier, email, password):
    embed = discord.Embed(
        title="🟣 GCart Delivery",
        description=(
            "<a:400125purplebook:1447592335012532334> **GCart Delivery**\n\n"
            f"<a:Neysi:1447993564079325267> **{gen_name.upper()} Account**\n"
            f"<a:Angry_Ping_Happy:1387445548780486816> From **{tier.upper()} GEN**\n\n"
            "<a:CoolDoge:1387445675360522240> **Email**\n"
            f"```{email}```\n"
            "<a:CoolDoge:1387445675360522240> **Password**\n"
            f"```{password}```\n\n"
            "<a:Warningggg:1433042494471540836> **Must Do Vouch**\n"
            "➡ https://discord.gg/CNFyBV5VnG"
        ),
        color=0x9b59b6
    )
    embed.set_footer(text="GCart • Best Gen Server")
    return embed


# ---------------- GENERATE LOGIC ----------------

async def generate_account(interaction, tier, gen_name):
    stock = data["stock"].get(tier, {}).get(gen_name, [])

    if not stock:
        return await interaction.response.send_message(
            "❌ Out of stock.", ephemeral=True
        )

    account = stock.pop(0)
    save_data(data)

    embed = build_account_embed(
        gen_name, tier, account["email"], account["password"]
    )

    try:
        await interaction.user.send(embed=embed)
        await interaction.response.send_message(
            "✅ Check your DM!", ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Your DMs are closed.", ephemeral=True
        )


# ---------------- VIEWS ----------------

class FreeMenu(discord.ui.View):
    @discord.ui.button(label="MCFA", style=discord.ButtonStyle.green)
    async def mcfa(self, interaction, button):
        await generate_account(interaction, "free", "mcfa")

    @discord.ui.button(label="Nitro Unchecked", style=discord.ButtonStyle.green)
    async def nitro(self, interaction, button):
        await generate_account(interaction, "free", "nitro_unchecked")


class VipMenu(discord.ui.View):
    @discord.ui.button(label="Steam", style=discord.ButtonStyle.blurple)
    async def steam(self, interaction, button):
        await generate_account(interaction, "vip", "steam")

    @discord.ui.button(label="MCFA", style=discord.ButtonStyle.blurple)
    async def mcfa(self, interaction, button):
        await generate_account(interaction, "vip", "mcfa")


class BoosterMenu(discord.ui.View):
    @discord.ui.button(label="GTA 5", style=discord.ButtonStyle.red)
    async def gta(self, interaction, button):
        await generate_account(interaction, "booster", "gta5")

    @discord.ui.button(label="GameKey", style=discord.ButtonStyle.red)
    async def gamekey(self, interaction, button):
        await generate_account(interaction, "booster", "gamekey")


class MainMenu(discord.ui.View):
    @discord.ui.button(label="🆓 Free Gen", style=discord.ButtonStyle.green)
    async def free(self, interaction, button):
        if not has_required_status(interaction.user):
            return await interaction.response.send_message(
                "❌ Required status missing.", ephemeral=True
            )
        await interaction.response.send_message(
            "Choose Free Generator:", view=FreeMenu(), ephemeral=True
        )

    @discord.ui.button(label="💎 VIP Gen", style=discord.ButtonStyle.blurple)
    async def vip(self, interaction, button):
        if not has_required_status(interaction.user):
            return await interaction.response.send_message(
                "❌ Required status missing.", ephemeral=True
            )
        if not has_role(interaction.user, data["roles"]["vip"]):
            return await interaction.response.send_message(
                "❌ VIP role required.", ephemeral=True
            )
        await interaction.response.send_message(
            "Choose VIP Generator:", view=VipMenu(), ephemeral=True
        )

    @discord.ui.button(label="🚀 Booster Gen", style=discord.ButtonStyle.red)
    async def booster(self, interaction, button):
        if not has_required_status(interaction.user):
            return await interaction.response.send_message(
                "❌ Required status missing.", ephemeral=True
            )
        if not has_role(interaction.user, data["roles"]["booster"]):
            return await interaction.response.send_message(
                "❌ Booster role required.", ephemeral=True
            )
        await interaction.response.send_message(
            "Choose Booster Generator:", view=BoosterMenu(), ephemeral=True
        )


# ---------------- COMMAND ----------------

@bot.command()
async def gen(ctx):
    await ctx.send("🎁 **Select Generator**", view=MainMenu())


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


bot.run(TOKEN)
