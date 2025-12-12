# main.py - GCart with Free/VIP/Booster tiers + tier-specific embeds + bulk-add
# Put your bot token in env var TOKEN (Railway)
# Edit VIP_ROLE_NAME, BOOSTER_ROLE_NAME, ADMIN_ROLE_NAME, REQUIRED_STATUS_PHRASE, SUPPORT_URL as needed.

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

REQUIRED_STATUS_PHRASE = ".gg/CNFyBV5VnG GCart Best Generator ✅"

ADMIN_ROLE_NAME = "GCartAdmin"
VIP_ROLE_NAME = "VIP"
BOOSTER_ROLE_NAME = "Booster"

SUPPORT_URL = "https://discord.gg/CNFyBV5VnG"

GEN_COLORS = {
    "mcfa": 0xF1C40F,
    "mcfa_banned": 0xE74C3C,
    "mcfa_unbanned": 0x2ECC71,
    "unchecked_nitro": 0x9AD0F5,
    "netflix": 0xE50914,
    "steam": 0x1B2838,
    "gta5": 0x2ECC71,
    "gamekey": 0x9B59B6,
    "donut_unbanned": 0x9B59B6,
    "xbox": 0x6C8EBF
}
DEFAULT_COLOR = 0xF1C40F

COOLDOWN_SECONDS = 200
last_used = {}

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
            "generators": {
                # start empty; fill via admin commands or replace file
                "mcfa": {"tier": "free", "accounts": [{"email":"jasdja@gmail.com","password":"sajsj"}]},
                "mcfa_banned": {"tier": "free", "accounts": []},
                "unchecked_nitro": {"tier": "free", "accounts": []},
                "mcfa_unbanned": {"tier": "vip", "accounts": []},
                "donut_unbanned": {"tier": "vip", "accounts": []},
                "steam": {"tier": "vip", "accounts": []},
                "gamekey": {"tier": "vip", "accounts": []},
                "gta5": {"tier": "vip", "accounts": []},
                "xbox": {"tier": "vip", "accounts": []},
                "booster_all": {"tier": "booster", "accounts": []}
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
def is_admin_member(member: discord.Member) -> bool:
    try:
        if member.guild_permissions.administrator:
            return True
    except Exception:
        pass
    try:
        return any(r.name == ADMIN_ROLE_NAME for r in member.roles)
    except Exception:
        return False

def is_admin_ctx(ctx) -> bool:
    return is_admin_member(ctx.author)

def member_has_role_by_name(member: discord.Member, role_name: str) -> bool:
    if not role_name:
        return False
    try:
        for r in member.roles:
            if r.name == role_name:
                return True
    except Exception:
        pass
    return False

def user_has_required_custom_status(member: discord.Member, phrase: str) -> bool:
    try:
        phrase = (phrase or "").lower().strip()
    except Exception:
        phrase = ""

    activities = getattr(member, "activities", None) or []
    collected = []

    for act in activities:
        try:
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

    try:
        if member.nick and phrase and phrase in member.nick.lower():
            return True
        if member.display_name and phrase and phrase in member.display_name.lower():
            return True
    except Exception:
        pass

    for s in collected:
        if ".gg/" in s or "gcart" in s:
            return True

    return False

def build_embed_for_tier(user: discord.User, gen: str, account: dict, tier: str) -> discord.Embed:
    """
    Build different DM embed content per tier.
    """
    gen = gen.upper()
    color = GEN_COLORS.get(gen.lower(), DEFAULT_COLOR)

    if tier == "free":
        title_line = "# 🎉 GCart Delivery Is Here!"
        subtitle = "> Thanks for generating. Here is your free account:"
    elif tier == "vip":
        title_line = "# 👑 VIP Delivery Is Here!"
        subtitle = "> ✨ U GOT ACCOUNT (VIP GEN) — Congrats! Here is your VIP account:"
    elif tier == "booster":
        title_line = "# 🔥 BOOSTER Delivery Is Here!"
        subtitle = "> 🚀 BOOSTER GEN — Exclusive account delivered! Enjoy:"
    else:
        title_line = "# 🎉 GCart Delivery Is Here!"
        subtitle = "> Here is your account:"

    description = (
        f"{title_line}\n"
        f"{subtitle}\n\n"
        f"**🔧 Generator:** **{gen}**\n\n"
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
        embed.set_footer(text=f"GCart • {tier.capitalize()} Gen", icon_url=bot.user.display_avatar.url)
    except Exception:
        embed.set_footer(text=f"GCart • {tier.capitalize()} Gen")
    embed.timestamp = discord.utils.utcnow()
    return embed

# Support View
class SupportOnlyView(ui.View):
    def __init__(self, timeout: int = 180):
        super().__init__(timeout=timeout)
        try:
            btn = ui.Button(label="Support", style=ButtonStyle.link, url=SUPPORT_URL)
            self.add_item(btn)
        except Exception:
            pass

# Tier permission check (roles-only)
def can_generate(member: discord.Member, generator_name: str) -> (bool, str):
    if is_admin_member(member):
        return True, ""
    gens = data.get("generators", {})
    gen = gens.get(generator_name)
    if not gen:
        return False, "Generator not found."
    tier = gen.get("tier", "free").lower()
    # booster role can access everything
    if member_has_role_by_name(member, BOOSTER_ROLE_NAME):
        return True, ""
    if tier == "free":
        return True, ""
    if tier == "vip":
        if member_has_role_by_name(member, VIP_ROLE_NAME):
            return True, ""
        return False, f"You need the **{VIP_ROLE_NAME}** role to generate VIP items."
    if tier == "booster":
        if member_has_role_by_name(member, BOOSTER_ROLE_NAME):
            return True, ""
        return False, f"You need the **{BOOSTER_ROLE_NAME}** role to generate Booster items."
    return False, "Access denied by tier."

# ======================
# COMMANDS
# ======================
@bot.command(name="help")
async def help_cmd(ctx):
    msg = f"""
GCart Bot Commands

USER:
  {PREFIX}gcart gen <generator>
  {PREFIX}gcart stock
  {PREFIX}debugstatus

ADMIN:
  {PREFIX}gen add <generator> <email> <password>
  {PREFIX}gen remove <generator> <index>
  {PREFIX}gen list <generator>
  {PREFIX}gcart creategen <generator> <tier>
  {PREFIX}gcart deletegen <generator>
  {PREFIX}gcart setstatusphrase <text>

BULK ADD (admin):
  {PREFIX}gen bulkadd <generator> <paste block>
    - Paste lines with "email password" per line (password may contain spaces).
    OR attach a text/CSV file to the command; bot will read the attachment.
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

    allowed, reason = can_generate(ctx.author, gen)
    if not allowed:
        await ctx.send(f"{ctx.author.mention} {reason}")
        return

    # custom status check for non-admins
    required_status = data.get("required_status_phrase", REQUIRED_STATUS_PHRASE)
    if not is_admin_ctx(ctx):
        if not user_has_required_custom_status(ctx.author, required_status):
            await ctx.send(f"{ctx.author.mention} Please set your custom status to include:\n`{required_status}`\n\nTips: include `.gg/` link or `gcart` anywhere in your status.")
            return

    # cooldown
    if not is_admin_ctx(ctx):
        now = time.time()
        last = last_used.get(ctx.author.id, 0)
        remaining = COOLDOWN_SECONDS - (now - last)
        if remaining > 0:
            await ctx.send(f"{ctx.author.mention} ⏳ Please wait **{int(remaining)}s** before generating again.")
            return
        last_used[ctx.author.id] = now

    gen_info = data["generators"][gen]
    accounts = gen_info.get("accounts", [])
    if not accounts:
        await ctx.send("⚠ No stock available.")
        return

    account = random.choice(accounts)
    tier = gen_info.get("tier", "free")
    embed = build_embed_for_tier(ctx.author, gen, account, tier)
    view = SupportOnlyView()
    try:
        await ctx.author.send(embed=embed, view=view)
        await ctx.send(f"✨ {ctx.author.mention} Check your DMs — your account has been sent!")
    except discord.Forbidden:
        await ctx.send("⚠ Please enable DMs from server members!")

@gcart_group.command(name="stock")
async def gcart_stock(ctx):
    embed = discord.Embed(title="📦 GCart Stock", color=0xF1C40F)
    gens = data.get("generators", {})
    tiers = {"free": [], "vip": [], "booster": []}
    for name, info in gens.items():
        t = info.get("tier", "free").lower()
        tiers.setdefault(t, []).append((name, len(info.get("accounts", []))))
    for t in ("free", "vip", "booster"):
        items = tiers.get(t, [])
        if not items:
            continue
        text = "\n".join([f"🔹 **{n.upper()}** — {count} in stock" for n, count in items])
        embed.add_field(name=f"{t.upper()} GENERATORS", value=text, inline=False)
    await ctx.send(embed=embed)

# --------------- admin group ---------------
@bot.group(name="gen", invoke_without_command=True)
async def gen_group(ctx):
    await ctx.send("Admin: add / remove / list / bulkadd")

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
    # if too long, DM to admin
    if len(msg) > 1900:
        await ctx.author.send("Full list:", file=None)
        chunks = [msg[i:i+1900] for i in range(0, len(msg), 1900)]
        for c in chunks:
            await ctx.author.send(f"```\n{c}\n```")
        await ctx.send("Sent full list to your DMs.")
    else:
        await ctx.send(f"```{msg}```")

@gen_group.command(name="bulkadd")
async def bulk_add(ctx, generator: str, *, pasted: str = None):
    """
    Bulk add accounts to a generator.
    Usage:
      1) Paste multiple lines after the command:
         !gen bulkadd mcfa
         (then paste lines in same message)
      2) Or attach a .txt/.csv file to the command (first attachment will be read).
    Format per line:
      email password
    If password contains spaces, it will take everything after first whitespace as password.
    """
    if not is_admin_ctx(ctx):
        return await ctx.send("❌ Permission denied.")
    gen = generator.lower()
    if gen not in data["generators"]:
        return await ctx.send("Generator doesn't exist.")

    text = ""
    # prefer attachment if present
    if ctx.message.attachments:
        try:
            att = ctx.message.attachments[0]
            raw = await att.read()
            text = raw.decode("utf-8", errors="ignore")
        except Exception as e:
            return await ctx.send(f"Failed to read attachment: {e}")
    else:
        # if no attachment, use pasted argument
        if not pasted:
            return await ctx.send("No data provided. Attach a .txt file or paste lines after the command.")
        text = pasted

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    added = 0
    errors = []
    for i, line in enumerate(lines):
        # support CSV or space-separated
        if "," in line:
            parts = [p.strip() for p in line.split(",", 1)]
        else:
            parts = line.split(None, 1)  # split on first whitespace: email, rest
        if len(parts) == 0:
            continue
        if len(parts) == 1:
            errors.append((i+1, "missing password"))
            continue
        email = parts[0].strip()
        password = parts[1].strip()
        if not email or not password:
            errors.append((i+1, "invalid email/password"))
            continue
        data["generators"][gen].setdefault("accounts", []).append({"email": email, "password": password})
        added += 1

    save_data(data)
    msg = f"Bulk add finished. Added {added} accounts to `{gen}`."
    if errors:
        msg += " Some lines failed:\n" + ", ".join([f"line{ln}:{why}" for ln, why in errors])
    await ctx.send(msg)

# create generator with tier
@gcart_group.command(name="creategen")
async def create_gen(ctx, generator: str, tier: str = "free"):
    if not is_admin_ctx(ctx):
        return await ctx.send("❌ Permission denied.")
    gen = generator.lower()
    tier = tier.lower()
    if tier not in ("free", "vip", "booster"):
        return await ctx.send("Tier must be one of: free, vip, booster")
    if gen in data["generators"]:
        return await ctx.send("Generator already exists.")
    data["generators"][gen] = {"tier": tier, "accounts": []}
    save_data(data)
    await ctx.send(f"Created generator `{gen}` with tier `{tier}`.")

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
        print(f"DEBUG: TOKEN_PRESENT={bool(TOKEN)} TOKEN_LEN={len(TOKEN) if TOKEN else 0}", flush=True)
    if not TOKEN:
        print("ERROR: TOKEN environment variable is missing. Please add TOKEN to your Railway service variables.")
    else:
        bot.run(TOKEN)
