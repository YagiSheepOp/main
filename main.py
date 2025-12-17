import discord
from discord.ext import commands
import json
import random

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!gcart ", intents=intents, help_command=None)

# ---------------- LOAD DATA ----------------
def load_data():
    with open("data.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

# ---------------- UTIL ----------------
def has_status(member):
    if not member.activity:
        return False
    return data["required_status"] in str(member.activity)

def has_role(member, role_name):
    return any(r.name == role_name for r in member.roles)

def account_embed(title, email, password):
    return discord.Embed(
        title=title,
        description=f"""
<a:400125purplebook:1447592335012532334> **GCart Delivery**
<a:Neysi:1447993564079325267> Your Account

📧 **Email**
```{email}

🔑 **Password**
```{}

<a:Warningggg:1433042494471540836> **Must Do Vouch**
➡ https://discord.gg/CNFyBV5VnG
""",
        color=0x9b59b6
    )

# ---------------- BUTTON VIEWS ----------------
class MainMenu(discord.ui.View):
    @discord.ui.button(label="🆓 Free Gen", style=discord.ButtonStyle.green)
    async def free(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_status(interaction.user):
            return await interaction.response.send_message(
                "❌ Status missing", ephemeral=True
            )
        await interaction.response.send_message(
            "Choose Free Stock:", view=FreeMenu(), ephemeral=True
        )

    @discord.ui.button(label="💎 VIP Gen", style=discord.ButtonStyle.blurple)
    async def vip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_status(interaction.user):
            return await interaction.response.send_message("❌ Status missing", ephemeral=True)
        if not has_role(interaction.user, data["roles"]["vip"]):
            return await interaction.response.send_message("❌ VIP role required", ephemeral=True)

        await interaction.response.send_message(
            "Choose VIP Stock:", view=VipMenu(), ephemeral=True
        )

    @discord.ui.button(label="🚀 Booster Gen", style=discord.ButtonStyle.red)
    async def booster(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_status(interaction.user):
            return await interaction.response.send_message("❌ Status missing", ephemeral=True)
        if not has_role(interaction.user, data["roles"]["booster"]):
            return await interaction.response.send_message("❌ Booster role required", ephemeral=True)

        await interaction.response.send_message(
            "Choose Booster Stock:", view=BoosterMenu(), ephemeral=True
        )

class FreeMenu(discord.ui.View):
    @discord.ui.button(label="MCFA", style=discord.ButtonStyle.green)
    async def mcfa(self, interaction, button):
        await generate(interaction, "free", "mcfa")

class VipMenu(discord.ui.View):
    @discord.ui.button(label="Steam", style=discord.ButtonStyle.blurple)
    async def steam(self, interaction, button):
        await generate(interaction, "vip", "steam")

class BoosterMenu(discord.ui.View):
    @discord.ui.button(label="GTA 5", style=discord.ButtonStyle.red)
    async def gta(self, interaction, button):
        await generate(interaction, "booster", "gta5")

# ---------------- GENERATE ----------------
async def generate(interaction, tier, name):
    stock = data["stock"][tier].get(name, [])
    if not stock:
        return await interaction.response.send_message("❌ Out of stock", ephemeral=True)

    acc = stock.pop(0)
    save_data(data)

    embed = account_embed("🎁 GCart Generator", acc["email"], acc["password"])
    try:
        await interaction.user.send(embed=embed)
        await interaction.response.send_message("✅ Check your DM", ephemeral=True)
    except:
        await interaction.response.send_message("❌ DM closed", ephemeral=True)

# ---------------- COMMANDS ----------------
@bot.command()
async def gen(ctx):
    await ctx.send("Select Generator:", view=MainMenu())

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ---------------- RUN ----------------
bot.run("YOUR_BOT_TOKEN")
