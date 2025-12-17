import discord
from discord.ext import commands
from discord.ui import View, Button
import json, os, random, time

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!gcart ", intents=intents)

DATA_FILE = "data.json"
with open(DATA_FILE, "r") as f:
    DATA = json.load(f)

REQUIRED_STATUS = DATA["required_status"]
COOLDOWN = DATA["cooldown_seconds"]
LAST_USED = {}

def save():
    with open(DATA_FILE, "w") as f:
        json.dump(DATA, f, indent=2)

def is_owner(ctx):
    return ctx.guild.owner_id == ctx.author.id

def has_status(member):
    if not member.activities:
        return False
    for a in member.activities:
        if isinstance(a, discord.CustomActivity) and a.name:
            if REQUIRED_STATUS in a.name:
                return True
    return False

def cooldown_ok(user):
    now = time.time()
    last = LAST_USED.get(user.id, 0)
    if now - last < COOLDOWN:
        return False, int(COOLDOWN - (now - last))
    LAST_USED[user.id] = now
    return True, 0

def make_embed(title, desc):
    return discord.Embed(
        title=title,
        description=desc,
        color=0x7d5fff
    )

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ---------------- GEN MENU ----------------

@bot.command()
async def gen(ctx):
    view = View(timeout=30)

    async def free_btn(inter):
        await handle_gen(inter, "free")

    async def vip_btn(inter):
        await handle_gen(inter, "vip")

    async def booster_btn(inter):
        await handle_gen(inter, "booster")

    view.add_item(Button(label="Free Gen", style=discord.ButtonStyle.green, callback=free_btn))
    view.add_item(Button(label="VIP Gen", style=discord.ButtonStyle.blurple, callback=vip_btn))
    view.add_item(Button(label="Booster Gen", style=discord.ButtonStyle.red, callback=booster_btn))

    await ctx.send(
        embed=make_embed("🎁 Select Generator", "Choose a generator below"),
        view=view,
        delete_after=30
    )

# ---------------- CORE GEN LOGIC ----------------

async def handle_gen(inter, tier):
    member = inter.user

    if not is_owner(inter):
        ok, wait = cooldown_ok(member)
        if not ok:
            return await inter.response.send_message(
                f"⏳ Cooldown: wait `{wait}s`", ephemeral=True
            )

        if not has_status(member):
            return await inter.response.send_message(
                embed=make_embed(
                    "❌ Status Missing",
                    "<a:animatedarrowgreen:1450811653552607296> Use this status:\n"
                    "```.gg/CNFyBV5VnG Best Gen & Best Server ✅```"
                ),
                ephemeral=True
            )

        if tier == "vip" and DATA["roles"]["vip"] not in [r.name for r in member.roles]:
            return await inter.response.send_message(
                embed=make_embed(
                    "⚠️ No VIP Role",
                    "<a:Warning:1450809908013563918> You do not have VIP\n"
                    "<a:animatedarrowgreen:1450811653552607296> Buy VIP from store"
                ),
                ephemeral=True
            )

        if tier == "booster" and DATA["roles"]["booster"] not in [r.name for r in member.roles]:
            return await inter.response.send_message(
                embed=make_embed(
                    "⚠️ No Booster Role",
                    "<a:Warning:1450809908013563918> Boost server to unlock Booster Gen"
                ),
                ephemeral=True
            )

    gens = DATA["generators"][tier]
    name = random.choice(list(gens.keys()))
    if not gens[name]:
        return await inter.response.send_message("❌ Out of stock.", ephemeral=True)

    acc = gens[name].pop(0)
    save()

    dm = make_embed(
        "<a:400125purplebook:1447592335012532334> **GCart Delivery**",
        f"<a:Neysi:1447993564079325267> **Your {name.upper()} Account**\n\n"
        f"📧 Email:\n```{acc['email']}```\n"
        f"🔑 Password:\n```{acc['password']}```\n\n"
        "<a:Warningggg:1433042494471540836> **Must Do Vouch**"
    )

    await member.send(embed=dm)
    await inter.response.send_message("✅ Check your DM!", ephemeral=True)

    if tier == "booster" and random.randint(1, 100) <= 5:
        vip_role = discord.utils.get(inter.guild.roles, name=DATA["roles"]["vip"])
        if vip_role:
            await member.add_roles(vip_role)

# ---------------- ADMIN ----------------

@bot.command()
@commands.has_permissions(administrator=True)
async def add(ctx, tier, name, email, password):
    DATA["generators"][tier][name].append({"email": email, "password": password})
    save()
    await ctx.send("✅ Account added.")

@bot.command()
@commands.has_permissions(administrator=True)
async def bulk(ctx, tier, name):
    if not ctx.message.attachments:
        return await ctx.send("Upload .txt file")

    file = await ctx.message.attachments[0].read()
    lines = file.decode().splitlines()

    for l in lines:
        if ":" in l:
            e, p = l.split(":", 1)
            DATA["generators"][tier][name].append({"email": e, "password": p})

    save()
    await ctx.send("✅ Bulk added.")

@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, tier, name):
    DATA["generators"][tier][name].clear()
    save()
    await ctx.send("🗑 Cleared.")

@bot.command()
@commands.has_permissions(administrator=True)
async def stock(ctx):
    text = ""
    for t, g in DATA["generators"].items():
        text += f"\n**{t.upper()}**\n"
        for n, a in g.items():
            text += f"{n}: {len(a)}\n"
    await ctx.send(f"```{text}```")

# ---------------- RUN ----------------

bot.run(os.getenv("DISCORD_TOKEN"))
