# main.py - GCart (Status-only verification)
# - Requires users to have a custom status containing either:
#     * the configured REQUIRED_STATUS_PHRASE (substring match)
#     * any ".gg/" shortlink (e.g. .gg/CNFyBV5VnG)
#     * the word "gcart"
# - Server tag checks removed
# - Admins (server administrators or role name ADMIN_ROLE_NAME) bypass cooldown & checks
# - Put your token in env var TOKEN (Railway). Do NOT hardcode token.

import os
import json
import random
import time
import discord
from discord.ext import commands
from discord import ui, ButtonStyle

# ======================
# CONFIG - edit these
# ======================
PREFIX = "!"
DATA_FILE = "data.json"

# REQUIRED custom status phrase (case-insensitive substring)
REQUIRED_STATUS_PHRASE = ".gg/CNFyBV5VnG GCart Best Generator ✅"

# Admin role name that bypasses checks and cooldown (case-sensitive)
ADMIN_ROLE_NAME = "GCartAdmin"

# Support invite / URL (must start with http(s) or a valid discord invite url)
SUPPORT_URL = "https://discord.gg/CNFyBV5VnG"

# Colors per generator (hex)
GEN_COLORS = {
    "mcfa": 0xF1C40F,
    "netflix": 0xE50914,
    "steam": 0x1B2838,
    "gta5": 0x2ECC71,
    "jiocinema": 0x00A3E0,
    "crunchyroll": 0xFF7F00,
    "gamekey": 0x9B59B6
}
DEFAULT_COLOR = 0xF1C40F

# Cooldown seconds for normal users (admins bypass)
COOLDOWN_SECONDS = 200
last_used = {}  # in-memory: user_id -> timestamp

# Optional debug (set DEBUG_LOG=1 in env to print token presence/len safely)
DEBUG_LOG = os.getenv("DEBUG_LOG", "0") == "1"

# ======================
# INTENTS & BOT
# ======================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ======================
# DATA LOAD / SAVE
# ======================
def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "required_status_phrase": REQUIRED_STATUS_PHRASE,
            "templates": {"stock_embed_footer": "Powered by GCart Bot"},
            "generators": {
                "mcfa": {"accounts": [{"email": "jasdja@gmail.com", "password": "sajsj"}]},
                "netflix": {"accounts": []},
                "steam": {"accounts": []},
                "jiocinema": {"accounts": []},
                "crunchyroll": {"accounts": []},
                "gta5": {"accounts": []},
                "gamekey": {"accounts": []}
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
data.setdefault("required_status_phrase", REQUIRED_STATUS_PHRASE)
save_data(data)

# ======================
# HELPERS
# ======================
def is_admin_ctx(ctx):
    try:
        if ctx.author.guild_permissions.administrator:
            return True
    except Exception:
        pass
    # role name bypass
    return ADMIN_ROLE_NAME in [r.name for r in ctx.author.roles]

def is_admin_member(member: discord.Member):
    try:
        if member.guild_permissions.administrator:
            return True
    except Exception:
        pass
    return ADMIN_ROLE_NAME in [r.name for r in getattr(member, "roles", [])]

def user_has_required_custom_status(member: discord.Member, phrase: str) -> bool:
    """
    Tolerant status check:
      - returns True if status contains the configured phrase (substring, case-insensitive)
      - OR if it contains ".gg/" (any invite shortlink)
      - OR if it contains "gcart"
    Also falls back to checking display_name and nick if presence isn't available.
    """
    try:
        phrase = (phrase or "").lower().strip()
    except Exception:
        phrase = ""

    activities = getattr(member, "activities", None) or []
    collected = []

    for act in activities:
        try:
            # check common fields
            state = getattr(act, "state", None)
            name = getattr(act, "name", None)
            text_options = [state, name, str(act)]
            for txt in text_options:
                if not txt:
                    continue
                s = str(txt).lower()
                collected.append(s)
                if phrase and phrase in s:
                    return True
                if ".gg/" in s:
                    return True
                if "gcart" in s:
                    return True
        except Exception:
            continue

    # fallback: check nick / display_name
    try:
        if member.nick and phrase and phrase in member.nick.lower():
            return True
        if member.display_name and phrase and phrase in member.display_name.lower():
            return True
    except Exception:
        pass

    # final fallback: check any collected text for .gg/ or gcart
    for s in collected:
        if ".gg/" in s or "gcart" in s:
            return True

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
    except Exception:
        pass
    try:
        embed.set_footer(text="GCart • Ultra Premium", icon_url=bot.user.display_avatar.url)
    except Exception:
        embed.set_footer(text="GCart • Ultra Premium")
    embed.timestamp = discord.utils.utcnow()
    return embed

# ======================
# BUTTON VIEW (Support only)
# ======================
class SupportOnlyView(ui.View):
    def __init__(self, timeout: int = 180):
        super().__init__(timeout=timeout)
        try:
            btn = ui.Button(label="Support", style=ButtonStyle.link, url=SUPPORT_URL)
            self.add_item(btn)
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
  {PREFIX}gen add <generator> <email> <password>
  {PREFIX}gen remove <generator> <index>
  {PREFIX}gen list <generator>
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

    # 1) check required custom status (only this check now)
    required_status = data.get("required_status_phrase", REQUIRED_STATUS_PHRASE)
    if not is_admin_ctx(ctx):  # admins bypass check (owner/administrator/role)
        if not user_has_required_custom_status(ctx.author, required_status):
            await ctx.send(f"{ctx.author.mention} Please set your custom status to include:\n`{required_status}`\n\nTips: include `.gg/` link or `gcart` anywhere in your status.")
            return

    # 2) cooldown (admins bypass)
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

# --------------- admin group ---------------
@bot.group(name="gen", invoke_without_command=True)
async def gen_group(ctx):
    await ctx.send("Admin: add / remove / list")

@gen_group.command(name="add")
async def add_acc(ctx, generator: str, email: str, password: str):
    if not is_admin_ctx(ctx):
        return await ctx.send("❌ Permission denied.")
    gen = generator.lower()
    if gen not in data["generators"]:
        return await ctx.send("Generator doesn't exist.")
    data["generators"][gen]["accounts"].append({"email": email, "password": password})
    save_data(data)
    await ctx.send("Added.")

@gen_group.command(name="remove")
async def remove_acc(ctx, generator: str, index: int):
    if not is_admin_ctx(ctx):
        return await ctx.send("❌ Permission denied.")
    gen = generator.lower()
    try:
        removed = data["generators"][gen]["accounts"].pop(index)
        save_data(data)
        await ctx.send(f"Removed {removed['email']}")
    except Exception:
        await ctx.send("Invalid index.")

@gen_group.command(name="list")
async def list_acc(ctx, generator: str):
    if not is_admin_ctx(ctx):
        return await ctx.send("❌ Permission denied.")
    gen = generator.lower()
    accounts = data["generators"].get(gen, {}).get("accounts", [])
    if not accounts:
        return await ctx.send("No accounts.")
    msg = "\n".join([f"{i}: {a['email']}" for i, a in enumerate(accounts)])
    await ctx.send(f"```{msg}```")

@gcart_group.command(name="creategen")
async def create_gen(ctx, generator: str):
    if not is_admin_ctx(ctx):
        return await ctx.send("❌ Permission denied.")
    gen = generator.lower()
    if gen in data["generators"]:
        return await ctx.send("Generator already exists.")
    data["generators"][gen] = {"accounts": []}
    save_data(data)
    await ctx.send(f"Created generator `{gen}`.")

@gcart_group.command(name="deletegen")
async def delete_gen(ctx, generator: str):
    if not is_admin_ctx(ctx):
        return await ctx.send("❌ Permission denied.")
    gen = generator.lower()
    if gen not in data["generators"]:
        return await ctx.send("Not found.")
    del data["generators"][gen]
    save_data(data)
    await ctx.send(f"Deleted `{gen}`.")

@gcart_group.command(name="setstatusphrase")
async def set_status_phrase(ctx, *, phrase: str):
    if not is_admin_ctx(ctx):
        return await ctx.send("❌ Permission denied.")
    data["required_status_phrase"] = phrase
    save_data(data)
    await ctx.send(f"Status updated to `{phrase}`")

# DEBUG
@bot.command(name="debugstatus")
async def debug_status(ctx):
    member = ctx.author
    acts = getattr(member, "activities", [])
    if not acts:
        await ctx.author.send("No activities — presence info not received.")
        return
    lines = []
    for a in acts:
        lines.append(f"repr: {repr(a)}\nstate={getattr(a,'state',None)} name={getattr(a,'name',None)}\n")
    await ctx.author.send("```\n" + "\n".join(lines) + "\n```")

# ON READY
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user} (ID: {bot.user.id})")

# RUN
if __name__ == "__main__":
    TOKEN = os.getenv("TOKEN")
    if DEBUG_LOG:
        # safe debug: presence + length only (never print token contents)
        print(f"DEBUG: TOKEN_PRESENT={bool(TOKEN)} TOKEN_LEN={len(TOKEN) if TOKEN else 0}", flush=True)
    if not TOKEN:
        print("ERROR: TOKEN environment variable is missing. Please add TOKEN to your Railway service variables.")
    else:
        bot.run(TOKEN)
