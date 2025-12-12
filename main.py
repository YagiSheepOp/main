# main.py - Fixed required-status + Ultra Premium GCart Bot (cooldown removed earlier)
import os
import json
import random
import time
import discord
from discord.ext import commands
from discord import ui, ButtonStyle

# ======================
# CONFIG
# ======================
PREFIX = "!"
DATA_FILE = "data.json"

# THE exact required status phrase (set this in your Discord custom status)
REQUIRED_STATUS_PHRASE = ".gg/CNFyBV5VnG GCart Best Generator ✅"

# admin role
ADMIN_ROLE_NAME = "GCartAdmin"

# Support button link (replace with your real invite or URL)
SUPPORT_URL = "https://discord.gg/CNFyBV5VnG"   # <-- replace with a valid URL

# Generator Colors
GEN_COLORS = {
    "mcfa": 0xF1C40F,
    "netflix": 0xE50914,
    "steam": 0x1B2838,
    "gta5": 0x2ECC71,
}
DEFAULT_COLOR = 0xF1C40F

# Cooldown seconds for non-admin users
COOLDOWN_SECONDS = 200

# In-memory cooldown tracker: user_id -> last_timestamp (float)
last_used = {}

# ======================
# INTENTS
# ======================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ======================
# LOAD/SAVE DATA
# ======================
def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "required_status_phrase": REQUIRED_STATUS_PHRASE,
            "templates": {"stock_embed_footer": "Powered by GCart Bot"},
            "generators": {
                "mcfa": {"accounts": [{"email": "jasdja@gmail.com", "password": "sajsj"}]},
                "netflix": {"accounts": []},
                "steam": {"accounts": []}
            }
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)

data = load_data()

# FORCE update the stored required phrase to the one you want (keeps it consistent)
data["required_status_phrase"] = REQUIRED_STATUS_PHRASE
save_data(data)

# ======================
# HELPERS
# ======================
def is_admin_ctx(ctx):
    if ctx.author.guild_permissions.administrator:
        return True
    return ADMIN_ROLE_NAME in [r.name for r in ctx.author.roles]

def is_admin_member(member: discord.Member):
    try:
        if member.guild_permissions.administrator:
            return True
    except Exception:
        pass
    return ADMIN_ROLE_NAME in [r.name for r in getattr(member, "roles", [])]

def user_has_required_custom_status(member: discord.Member, phrase: str) -> bool:
    phrase = phrase.lower()
    activities = getattr(member, "activities", None)
    if not activities:
        return False
    for act in activities:
        try:
            state = getattr(act, "state", None)
            if state and phrase in str(state).lower():
                return True
            name = getattr(act, "name", None)
            if name and phrase in str(name).lower():
                return True
            if phrase in str(act).lower():
                return True
        except:
            pass
    return False

def build_premium_embed(user, gen: str, account: dict) -> discord.Embed:
    color = GEN_COLORS.get(gen.lower(), DEFAULT_COLOR)
    description = (
        f"# 🎉 GCart Delivery Is Here!\n"
        f"> ✨ Your premium account has been generated successfully!\n\n"
        f"**🔧 Generator:** **{gen.upper()}**\n\n"
        f"📧 **Email:**\n```{account.get('email','N/A')}```\n\n"
        f"🔐 **Password:**\n```{account.get('password','N/A')}```\n\n"
        f"💛 *Powered by GCart Bot*"
    )
    embed = discord.Embed(description=description, color=color)
    try:
        embed.set_thumbnail(url=user.display_avatar.url)
    except:
        pass
    try:
        embed.set_footer(text="GCart • Ultra Premium", icon_url=bot.user.display_avatar.url)
    except:
        embed.set_footer(text="GCart • Ultra Premium")
    embed.timestamp = discord.utils.utcnow()
    return embed

# ======================
# SUPPORT BUTTON VIEW
# ======================
class SupportOnlyView(ui.View):
    def __init__(self, timeout: int = 180):
        super().__init__(timeout=timeout)
        try:
            support_btn = ui.Button(label="Support", style=ButtonStyle.link, url=SUPPORT_URL)
            self.add_item(support_btn)
        except Exception:
            pass

# ======================
# COMMANDS
# ======================
@bot.command(name="help")
async def help_cmd(ctx):
    msg = f"""
GCart Ultra Premium Bot Commands

USER:
  {PREFIX}gcart gen <generator>
  {PREFIX}gcart stock
  {PREFIX}debugstatus

ADMIN:
  {PREFIX}gen <generator> add <email> <password>
  {PREFIX}gen <generator> remove <index>
  {PREFIX}gen <generator> list
  {PREFIX}gcart creategen <generator>
  {PREFIX}gcart deletegen <generator>
  {PREFIX}gcart setstatusphrase <text>
"""
    await ctx.send(f"```{msg}```")

@bot.group(name="gcart", invoke_without_command=True)
async def gcart_group(ctx):
    await ctx.send(f"Use `{PREFIX}help` for commands.")

@gcart_group.command(name="gen")
async def gcart_gen(ctx, generator: str):
    gen = generator.lower()
    if gen not in data["generators"]:
        await ctx.send(f"⚠ Generator `{gen}` not found.")
        return

    # Use the forced/stored phrase (we wrote it earlier)
    required = data.get("required_status_phrase", REQUIRED_STATUS_PHRASE)
    if not user_has_required_custom_status(ctx.author, required):
        await ctx.send(f"{ctx.author.mention} Please set your custom status to include:\n`{required}`")
        return

    # Cooldown check (admins bypass)
    if not is_admin_ctx(ctx):
        now = time.time()
        last = last_used.get(ctx.author.id, 0)
        remaining = COOLDOWN_SECONDS - (now - last)
        if remaining > 0:
            await ctx.send(f"{ctx.author.mention} ⏳ Please wait **{int(remaining)}s** before generating again.")
            return
        last_used[ctx.author.id] = now

    accounts = data["generators"][gen]["accounts"]
    if not accounts:
        await ctx.send("⚠ No stock available.")
        return

    account = random.choice(accounts)
    embed = build_premium_embed(ctx.author, gen, account)
    view = SupportOnlyView()
    try:
        await ctx.author.send(embed=embed, view=view)
        await ctx.send(f"✨ {ctx.author.mention} Check your DMs — your premium account is ready!")
    except discord.Forbidden:
        await ctx.send("⚠ Please enable DMs from server members!")

@gcart_group.command(name="stock")
async def gcart_stock(ctx):
    embed = discord.Embed(title="📦 GCart Stock", color=0xF1C40F)
    for name, info in data["generators"].items():
        embed.add_field(name=f"🔹 {name.upper()}", value=f"**{len(info['accounts'])}** in stock", inline=False)
    await ctx.send(embed=embed)

# ADMIN GROUP
@bot.group(name="gen", invoke_without_command=True)
async def gen_group(ctx):
    await ctx.send("Admin: add / remove / list")

@gen_group.command(name="add")
async def add_acc(ctx, gen: str, email: str, password: str):
    if not is_admin_ctx(ctx):
        return await ctx.send("❌ Permission denied.")
    gen = gen.lower()
    if gen not in data["generators"]:
        return await ctx.send("Generator doesn't exist.")
    data["generators"][gen]["accounts"].append({"email": email, "password": password})
    save_data(data)
    await ctx.send("Added.")

@gen_group.command(name="remove")
async def remove_acc(ctx, gen: str, index: int):
    if not is_admin_ctx(ctx):
        return await ctx.send("❌ Permission denied.")
    gen = gen.lower()
    try:
        removed = data["generators"][gen]["accounts"].pop(index)
        save_data(data)
        await ctx.send(f"Removed {removed['email']}")
    except Exception:
        await ctx.send("Invalid index.")

@gen_group.command(name="list")
async def list_acc(ctx, gen: str):
    if not is_admin_ctx(ctx):
        return await ctx.send("❌ Permission denied.")
    accs = data["generators"][gen.lower()]["accounts"]
    if not accs:
        return await ctx.send("No accounts.")
    msg = "\n".join([f"{i}: {a['email']}" for i, a in enumerate(accs)])
    await ctx.send(f"```{msg}```")

@gcart_group.command(name="creategen")
async def cg(ctx, gen: str):
    if not is_admin_ctx(ctx):
        return await ctx.send("❌ Permission denied.")
    gen = gen.lower()
    data["generators"][gen] = {"accounts": []}
    save_data(data)
    await ctx.send("Generator created.")

@gcart_group.command(name="deletegen")
async def dg(ctx, gen: str):
    if not is_admin_ctx(ctx):
        return await ctx.send("❌ Permission denied.")
    gen = gen.lower()
    if gen in data["generators"]:
        del data["generators"][gen]
        save_data(data)
        await ctx.send("Generator deleted.")
    else:
        await ctx.send("Generator not found.")

@gcart_group.command(name="setstatusphrase")
async def ssp(ctx, *, phrase: str):
    if not is_admin_ctx(ctx):
        return await ctx.send("❌ Permission denied.")
    data["required_status_phrase"] = phrase
    save_data(data)
    await ctx.send(f"Status updated to `{phrase}`")

# DEBUG
@bot.command(name="debugstatus")
async def dbg(ctx):
    acts = getattr(ctx.author, "activities", [])
    out = ""
    for a in acts:
        out += f"{repr(a)}\nstate={getattr(a,'state',None)}\n\n"
    if not out:
        await ctx.author.send("No activities available — bot may not be receiving presence info.")
    else:
        await ctx.author.send(f"```\n{out}\n```")

# READY
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

# RUN
if __name__ == "__main__":
    token = "MTQ0ODY4MzkzNjgxNjU2NjQ0Nw.GwENVP.w1vy5i5jCvWZBvuLan9SAxCoFuwrZwfuglz7E0"   # <-- put bot token here
    if token.startswith("YOUR") or token.strip() == "":
        print("ERROR: Replace the token variable with your real bot token in the script.")
    else:
        bot.run(token)
