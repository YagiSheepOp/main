import discord
from discord.ext import commands
import json
import os

TOKEN = os.getenv("TOKEN")  # Railway env variable

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True

bot = commands.Bot(
    command_prefix="!gcart ",
    intents=INTENTS,
    help_command=None  # IMPORTANT: prevents help conflict
)

DATA_FILE = "data.json"


# -------------------- DATA UTILS --------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({
                "required_status_phrase": ".gg/CNFyBV5VnG Best Gen Server",
                "generators": {}
            }, f, indent=4)

    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def is_admin(member: discord.Member):
    return member.guild_permissions.administrator


# -------------------- BOT EVENTS --------------------

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Game(".gg/CNFyBV5VnG Best Gen Server")
    )
    print(f"✅ Logged in as {bot.user}")


# -------------------- HELP COMMAND --------------------

@bot.command()
async def help(ctx):
    if is_admin(ctx.author):
        await ctx.send(
            "**📌 GCart Admin Commands**\n"
            "```"
            "!gcart gen <name>\n"
            "!gcart stock\n"
            "!gcart create <genname> <free/vip/booster>\n"
            "!gcart add <free/vip/booster> <genname> <email> <password>\n"
            "!gcart bulk <free/vip/booster> <genname> (upload .txt)\n"
            "!gcart clear <free/vip/booster> <genname>\n"
            "!gcart dm @user <message>\n"
            "```"
        )
    else:
        await ctx.send(
            "**📌 GCart Commands**\n"
            "```"
            "!gcart gen <name>\n"
            "!gcart stock\n"
            "```"
        )


# -------------------- CREATE GENERATOR --------------------

@bot.command()
async def create(ctx, genname: str, tier: str):
    if not is_admin(ctx.author):
        return await ctx.send("❌ Admin only command.")

    tier = tier.lower()
    genname = genname.lower()

    if tier not in ["free", "vip", "booster"]:
        return await ctx.send("❌ Invalid tier.")

    data = load_data()

    if genname in data["generators"]:
        return await ctx.send("❌ Generator already exists.")

    data["generators"][genname] = {
        "tier": tier,
        "accounts": []
    }

    save_data(data)
    await ctx.send(f"✅ Generator `{genname}` created as `{tier}`.")


# -------------------- ADD ACCOUNT --------------------

@bot.command()
async def add(ctx, tier: str, genname: str, email: str, password: str):
    if not is_admin(ctx.author):
        return await ctx.send("❌ Admin only command.")

    tier = tier.lower()
    genname = genname.lower()

    data = load_data()

    if genname not in data["generators"]:
        return await ctx.send("❌ Generator not found.")

    if data["generators"][genname]["tier"] != tier:
        return await ctx.send("❌ Tier mismatch.")

    data["generators"][genname]["accounts"].append({
        "email": email,
        "password": password
    })

    save_data(data)
    await ctx.send(f"✅ Account added to `{genname}`.")


# -------------------- BULK ADD --------------------

@bot.command()
async def bulk(ctx, tier: str, genname: str):
    if not is_admin(ctx.author):
        return await ctx.send("❌ Admin only command.")

    if not ctx.message.attachments:
        return await ctx.send("❌ Upload a `.txt` file.")

    tier = tier.lower()
    genname = genname.lower()

    data = load_data()

    if genname not in data["generators"]:
        return await ctx.send("❌ Generator not found.")

    attachment = ctx.message.attachments[0]
    content = (await attachment.read()).decode()

    added = 0
    for line in content.splitlines():
        if ":" in line:
            email, password = line.split(":", 1)
            data["generators"][genname]["accounts"].append({
                "email": email.strip(),
                "password": password.strip()
            })
            added += 1

    save_data(data)
    await ctx.send(f"✅ Bulk added `{added}` accounts to `{genname}`.")


# -------------------- CLEAR STOCK --------------------

@bot.command()
async def clear(ctx, tier: str, genname: str):
    if not is_admin(ctx.author):
        return await ctx.send("❌ Admin only command.")

    genname = genname.lower()
    tier = tier.lower()

    data = load_data()

    if genname not in data["generators"]:
        return await ctx.send("❌ Generator not found.")

    data["generators"][genname]["accounts"] = []
    save_data(data)

    await ctx.send(f"🗑️ Cleared all stock for `{genname}`.")


# -------------------- STOCK --------------------

@bot.command()
async def stock(ctx):
    data = load_data()

    if not data["generators"]:
        return await ctx.send("❌ No generators found.")

    msg = "**📦 GCart Stock**\n"
    for name, info in data["generators"].items():
        msg += f"• `{name}` → `{len(info['accounts'])}`\n"

    await ctx.send(msg)


# -------------------- GENERATE --------------------

@bot.command()
async def gen(ctx, genname: str):
    genname = genname.lower()
    data = load_data()

    if genname not in data["generators"]:
        return await ctx.send("❌ Invalid generator name.")

    if not data["generators"][genname]["accounts"]:
        return await ctx.send("❌ Out of stock.")

    account = data["generators"][genname]["accounts"].pop(0)
    save_data(data)

    embed = discord.Embed(
        title="<a:400125purplebook:1447592335012532334> GCart Delivery <a:400125purplebook:1447592335012532334>",
        description=(
            f"<a:GUPE_FIRE:1450810302982783046> **Your `{genname.upper()}` Account Is Here** "
            f"<a:GUPE_FIRE:1450810302982783046>\n\n"
            f"<:MonkaS_ping:1450810680016896085> "
            f"You Generated Account From **{data['generators'][genname]['tier'].upper()} GEN** "
            f"<:MonkaS_ping:1450810680016896085>"
        ),
        color=0xffff00
    )

    embed.add_field(
        name="<a:dogdance:1450810869184462949> Email",
        value=f"```{account['email']}```",
        inline=False
    )

    embed.add_field(
        name="<a:dogdance:1450810869184462949> Password",
        value=f"```{account['password']}```",
        inline=False
    )

    embed.add_field(
        name="<a:Warning:1450809908013563918> Must Do Vouch",
        value=(
            "<a:animatedarrowgreen:1450811653552607296> "
            "https://discord.com/channels/1439302910134583580/1449070993195794545"
        ),
        inline=False
    )

    embed.set_footer(text="GCart • Best Gen Server")

    try:
        await ctx.author.send(embed=embed)
        await ctx.send("✅ **Check your DM!**")
    except discord.Forbidden:
        await ctx.send("❌ **Your DMs are closed.**")



# -------------------- DM COMMAND --------------------

@bot.command()
async def dm(ctx, user: discord.Member, *, msg: str):
    if not is_admin(ctx.author):
        return await ctx.send("❌ Admin only command.")

    try:
        await user.send(msg)
        await ctx.send("✅ DM sent.")
    except:
        await ctx.send("❌ Failed to send DM.")


# -------------------- RUN --------------------

bot.run(TOKEN)
