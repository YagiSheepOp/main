# main.py - GCart Ultra Premium (Status + Server Tag required)
# Edit the CONFIG block below (SUPPORT_URL, REQUIRED_STATUS_PHRASE, REQUIRED_SERVER_TAG, ADMIN_ROLE_NAME)
# Deploy on Railway: add TOKEN env var, Procfile: worker: python main.py

import os
import json
import random
import time
import discord
from discord.ext import commands
from discord import ui, ButtonStyle

# ======================
# CONFIG - EDIT THESE (only these 4 values are usually required)
# ======================
PREFIX = "!"
DATA_FILE = "data.json"

# REQUIRED custom status phrase (case-insensitive)
REQUIRED_STATUS_PHRASE = ".gg/CNFyBV5VnG GCart Best Generator ✅"

# REQUIRED server tag text (exact text users adopt). Change to your exact server tag text.
REQUIRED_SERVER_TAG = "GCrt"

# Admin role name that bypasses checks and cooldown
ADMIN_ROLE_NAME = "GCartAdmin"

# Support button link (must be a valid URL starting with http/https or discord invite)
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

# Optional debug flag: set env DEBUG_LOG=1 to print token presence and lengths (safe)
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
            "required_server_tag": REQUIRED_SERVER_TAG,
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
# sync config fields with file (so admin commands can update)
data.setdefault("required_status_phrase", REQUIRED_STATUS_PHRASE)
data.setdefault("required_server_tag", REQUIRED_SERVER_TAG)
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
    return ADMIN_ROLE_NAME in [r.name for r in ctx.author.roles]

def is_admin_member(member: discord.Member):
    try:
        if member.guild_permissions.administrator:
            return True
    except Exception:
        pass
    return ADMIN_ROLE_NAME in [r.name for r in getattr(member, "roles", [])]

def user_has_required_custom_status(member: discord.Member, phrase: str) -> bool:
    """Check for custom status text (robust across versions)."""
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
        except Exception:
            continue
    return False

def user_has_server_tag(member: discord.Member, tag_text: str) -> bool:
    """
    Try to detect Server Tag adoption.
    Strategy:
     1) Try member.guild_profile.* fields (if available)
     2) Try member.public_flags (not reliable)
     3) Fallback: check nickname/display_name contains tag substring
    """
    tag_text = tag_text.lower()
    # 1) guild_profile (newer API)
    try:
        gp = getattr(member, "guild_profile", None)
        if gp:
            for attr in ("badges", "tags", "server_tags", "tag_names"):
                val = getattr(gp, attr, None)
                if val:
                    try:
                        for item in val:
                            if isinstance(item, str):
                                if tag_text in item.lower():
                                    return True
                            elif isinstance(item, dict):
                                name = item.get("name") or item.get("label") or item.get("title")
                                if name and tag_text in str(name).lower():
                                    return True
                            else:
                                name = getattr(item, "name", None) or getattr(item, "label", None) or getattr(item, "title", None)
                                if name and tag_text in str(name).lower():
                                    return True
                    except Exception:
                        continue
    except Exception:
        pass

    # 2) public_flags
    try:
        pf = getattr(member, "public_flags", None)
        if pf:
            if tag_text in str(pf).lower():
                return True
    except Exception:
        pass

    # 3) fallback: check nick or display name
    try:
        nick = getattr(member, "nick", None)
        if nick and tag_text in nick.lower():
            return True
    except Exception:
        pass

    try:
        name = getattr(member, "display_name", None) or getattr(member, "name", None)
        if name and tag_text in name.lower():
            return True
    except Exception:
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

    # 1) check required custom status
    required_status = data.get("required_status_phrase", REQUIRED_STATUS_PHRASE)
    if not user_has_required_custom_status(ctx.author, required_status):
        await ctx.send(f"{ctx.author.mention} Please set your custom status to include:\n`{required_status}`")
        return

    # 2) check required server tag adoption
    required_tag = data.get("required_server_tag", REQUIRED_SERVER_TAG)
    if not user_has_server_tag(ctx.author, required_tag):
        await ctx.send(
            f"{ctx.author.mention} You must adopt the server tag **{required_tag}** to generate.\n"
            f"Go to: Server → Edit Server Profile → Server Tag → Adopt Tag."
        )
        return

    # 3) cooldown (admins bypass)
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

@gcart_group.command(name="setservertag")
async def set_server_tag(ctx, *, tag: str):
    """Admin: set required server tag text (exact)."""
    if not is_admin_ctx(ctx):
        return await ctx.send("❌ Permission denied.")
    data["required_server_tag"] = tag
    save_data(data)
    await ctx.send(f"Required server tag set to: `{tag}`")

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

@bot.command(name="debugservertag")
async def debug_server_tag(ctx):
    """Debug helper: show what we detect about server tag / guild_profile."""
    member = ctx.author
    out = []
    gp = getattr(member, "guild_profile", None)
    out.append(f"guild_profile: {bool(gp)}")
    if gp:
        for attr in ("badges","tags","server_tags","tag_names"):
            val = getattr(gp, attr, None)
            out.append(f"{attr}: {repr(val)}")
    out.append(f"nick: {member.nick}")
    out.append(f"display_name: {member.display_name}")
    await ctx.author.send("```\n" + "\n".join(out) + "\n```")

# ON READY
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user} (ID: {bot.user.id})")

# RUN
if __name__ == "__main__":
    # read token from env (Railway variable name must be TOKEN)
    TOKEN = os.getenv("TOKEN")

    # optional safe debug (prints presence and length, never the token)
    if DEBUG_LOG:
        print(f"DEBUG: TOKEN_PRESENT={bool(TOKEN)} TOKEN_LEN={len(TOKEN) if TOKEN else 0}", flush=True)

    if not TOKEN:
        print("ERROR: TOKEN environment variable is missing. Please add TOKEN to your Railway service variables.")
    else:
        bot.run(TOKEN)
T
