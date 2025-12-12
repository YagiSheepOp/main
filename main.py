# main.py
# GCart generator bot - free / vip / booster tiers
# - Put your bot token in env var "TOKEN" (Railway)
# - Edit VIP_ROLE_NAME / BOOSTER_ROLE_NAME / ADMIN_ROLE_NAME if needed
# - Uses prefix "!" for commands

import os
import json
import random
import time
import discord
from discord.ext import commands

# =============
# CONFIG
# =============
PREFIX = "!"
TOKEN_ENV_NAME = "TOKEN"

# required phrase in custom status (case-insensitive substring)
REQUIRED_STATUS_PHRASE = ".gg/CNFyBV5VnG"

# role names (match exactly in your server; change if different)
ADMIN_ROLE_NAME = "GCartAdmin"   # people with this role OR server admins bypass checks
VIP_ROLE_NAME = "VIP"
BOOSTER_ROLE_NAME = "Booster"

# cooldown seconds (for non-admins)
COOLDOWN_SECONDS = 200
last_used = {}

# data file
DATA_FILE = "data.json"

# intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# =============
# HELPERS (normalization & data)
# =============
def norm(name: str) -> str:
    """normalize generator names: lowercase, spaces -> underscore, remove invalid chars"""
    return name.strip().lower().replace(" ", "_").replace("-", "_")

def load_data():
    if not os.path.exists(DATA_FILE):
        # create starter file if missing (will be overwritten by provided data.json if you add it)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"required_status_phrase": REQUIRED_STATUS_PHRASE, "generators": {}}, f, indent=2)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)

data = load_data()
data.setdefault("required_status_phrase", REQUIRED_STATUS_PHRASE)
data.setdefault("generators", {})
save_data(data)

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

def has_role_by_name(member: discord.Member, role_name: str) -> bool:
    if not role_name:
        return False
    try:
        return any(r.name == role_name for r in member.roles)
    except Exception:
        return False

def user_has_required_status(member: discord.Member) -> bool:
    phrase = data.get("required_status_phrase", REQUIRED_STATUS_PHRASE) or ""
    phrase = phrase.lower().strip()
    # check activities
    try:
        acts = getattr(member, "activities", []) or []
        for a in acts:
            # many activity classes; check name/state/str
            try:
                for field in (getattr(a, "state", None), getattr(a, "name", None), str(a)):
                    if not field:
                        continue
                    s = str(field).lower()
                    if phrase and phrase in s:
                        return True
                    if ".gg/" in s:
                        return True
                    if "gcart" in s:
                        return True
            except Exception:
                continue
    except Exception:
        pass

    # fallback to display_name/nick
    try:
        if member.display_name and phrase and phrase in member.display_name.lower():
            return True
    except Exception:
        pass

    return False

def generator_exists(key: str) -> bool:
    key = norm(key)
    return key in data.get("generators", {})

def get_generator(key: str):
    key = norm(key)
    return data["generators"].get(key)

# =============
# EMBED BUILDER
# =============
def build_dm_embed(user: discord.User, generator_key: str, account: dict, tier: str) -> discord.Embed:
    # set different title/subtitle per tier
    genname = generator_key.upper()
    if tier == "free":
        title = "🎁 GCart Delivery Is Here!"
        subtitle = "Thanks for generating. Here is your free account:"
    elif tier == "vip":
        title = "👑 VIP Delivery Is Here!"
        subtitle = "✨ U GOT ACCOUNT (VIP GEN) — Congrats! Here is your VIP account:"
    elif tier == "booster":
        title = "🔥 BOOSTER Delivery Is Here!"
        subtitle = "🚀 BOOSTER GEN — Exclusive account delivered! Enjoy:"
    else:
        title = "🎁 GCart Delivery Is Here!"
        subtitle = "Here is your account:"

    email = account.get("email", "N/A")
    password = account.get("password", "N/A")

    description = f"**{title}**\n{subtitle}\n\n**Generator:** `{genname}`\n\n**Email:**\n```{email}```\n**Password:**\n```{password}```\n\n*Powered by GCart Bot*"
    embed = discord.Embed(description=description, color=0xF1C40F)
    try:
        embed.set_footer(text=f"GCart • {tier.capitalize()} Gen", icon_url=bot.user.display_avatar.url)
    except Exception:
        embed.set_footer(text=f"GCart • {tier.capitalize()} Gen")
    embed.timestamp = discord.utils.utcnow()
    try:
        embed.set_thumbnail(url=user.display_avatar.url)
    except Exception:
        pass
    return embed

# =============
# COMMANDS
# =============
@bot.command(name="help")
async def help_cmd(ctx):
    text = (
        "GCart Commands\n\n"
        "USER:\n"
        "  !gcart gen <generator>   - Generate an account (status + role checks apply)\n"
        "  !gcart stock             - Show current stock (counts by tier)\n"
        "  !debugstatus             - (DM) show what presence the bot sees for you\n\n"
        "ADMIN (server admin or GCartAdmin role):\n"
        "  !gen add <generator> <email> <password>\n"
        "  !gen remove <generator> <index>\n"
        "  !gen list <generator>\n"
        "  !gen bulkadd <generator> (attach .txt or paste lines in same message)\n"
        "  !gcart creategen <name> <tier>   (tier: free|vip|booster)\n"
        "  !gcart deletegen <name>\n"
        "  !gcart setstatusphrase <text>\n"
    )
    await ctx.send(f"```{text}```")

@bot.group(name="gcart", invoke_without_command=True)
async def gcart_group(ctx):
    await ctx.send("Use !help for commands.")

@gcart_group.command(name="gen")
async def gcart_gen(ctx, *, generator: str):
    key = norm(generator)
    if not generator_exists(key):
        await ctx.send("❌ Invalid generator name.")
        return

    gen = get_generator(key)
    tier = gen.get("tier", "free").lower()

    # role check
    if not is_admin_member(ctx.author):
        # booster role bypasses VIP
        if has_role_by_name(ctx.author, BOOSTER_ROLE_NAME):
            pass  # allowed
        else:
            if tier == "vip" and not has_role_by_name(ctx.author, VIP_ROLE_NAME):
                await ctx.send(f"⭐ You need the **{VIP_ROLE_NAME}** role to use this generator.")
                return
            if tier == "booster" and not has_role_by_name(ctx.author, BOOSTER_ROLE_NAME):
                await ctx.send(f"🚀 You need the **{BOOSTER_ROLE_NAME}** role to use this generator.")
                return

    # status check for non-admins
    if not is_admin_member(ctx.author):
        if not user_has_required_status(ctx.author):
            phrase = data.get("required_status_phrase", REQUIRED_STATUS_PHRASE)
            await ctx.send(f"{ctx.author.mention} Please set your custom status to include:\n`{phrase}`\n\nTip: include `.gg/` or `gcart` in your status.")
            return

    # cooldown (admins bypass)
    if not is_admin_member(ctx.author):
        now = time.time()
        last = last_used.get(ctx.author.id, 0)
        remaining = COOLDOWN_SECONDS - (now - last)
        if remaining > 0:
            await ctx.send(f"{ctx.author.mention} ⏳ Please wait **{int(remaining)}s** before generating again.")
            return
        last_used[ctx.author.id] = now

    accounts = gen.get("accounts", [])
    if not accounts:
        await ctx.send("⚠ No stock available for this generator.")
        return

    # choose random without removing by default — keep infinite loop behavior: if you want to remove, admin will control
    account = random.choice(accounts)

    embed = build_dm_embed(ctx.author, key, account, tier)
    try:
        await ctx.author.send(embed=embed)
        await ctx.send(f"✨ {ctx.author.mention} Check your DMs — account sent!")
    except discord.Forbidden:
        await ctx.send("⚠ I cannot DM you. Enable DMs from server members.")

@gcart_group.command(name="stock")
async def stock_cmd(ctx):
    embed = discord.Embed(title="📦 GCart Stock", color=0xF1C40F)
    gens = data.get("generators", {})
    tiers = {"free": [], "vip": [], "booster": []}
    for name, info in gens.items():
        t = info.get("tier", "free").lower()
        count = len(info.get("accounts", []))
        tiers.setdefault(t, []).append((name, count))
    for t in ("free", "vip", "booster"):
        items = tiers.get(t, [])
        if not items:
            continue
        lines = "\n".join([f"🔹 **{n}** — {c} in stock" for n, c in items])
        embed.add_field(name=f"{t.upper()} GENERATORS", value=lines, inline=False)
    await ctx.send(embed=embed)

# admin helpers
def require_admin(ctx):
    if is_admin_member(ctx.author) or ctx.author.guild_permissions.administrator:
        return True
    return False

@bot.group(name="gen", invoke_without_command=True)
async def gen_group(ctx):
    await ctx.send("Admin: use add/remove/list/bulkadd")

@gen_group.command(name="add")
async def gen_add(ctx, generator: str, email: str, password: str):
    if not require_admin(ctx):
        return await ctx.send("❌ Permission denied.")
    key = norm(generator)
    if not generator_exists(key):
        return await ctx.send("❌ Generator not found.")
    data["generators"][key].setdefault("accounts", []).append({"email": email, "password": password})
    save_data(data)
    await ctx.send("✅ Added account.")

@gen_group.command(name="remove")
async def gen_remove(ctx, generator: str, index: int):
    if not require_admin(ctx):
        return await ctx.send("❌ Permission denied.")
    key = norm(generator)
    if not generator_exists(key):
        return await ctx.send("❌ Generator not found.")
    try:
        removed = data["generators"][key]["accounts"].pop(index)
        save_data(data)
        await ctx.send(f"🗑 Removed {removed.get('email')}")
    except Exception:
        await ctx.send("❌ Invalid index.")

@gen_group.command(name="list")
async def gen_list(ctx, generator: str):
    if not require_admin(ctx):
        return await ctx.send("❌ Permission denied.")
    key = norm(generator)
    if not generator_exists(key):
        return await ctx.send("❌ Generator not found.")
    accounts = data["generators"][key].get("accounts", [])
    if not accounts:
        return await ctx.send("No accounts.")
    msg = "\n".join([f"{i}: {a.get('email')}" for i, a in enumerate(accounts)])
    if len(msg) > 1900:
        await ctx.author.send("Full list (long):")
        for i in range(0, len(msg), 1900):
            await ctx.author.send(msg[i:i+1900])
        await ctx.send("Sent full list to your DMs.")
    else:
        await ctx.send(f"```\n{msg}\n```")

@gen_group.command(name="bulkadd")
async def gen_bulkadd(ctx, generator: str, *, pasted: str = None):
    """
    Bulk add accounts. Admin only.
    Use:
     - attach a .txt/.csv file with lines like: email password
     - or paste lines after command
    """
    if not require_admin(ctx):
        return await ctx.send("❌ Permission denied.")
    key = norm(generator)
    if not generator_exists(key):
        return await ctx.send("❌ Generator not found.")
    text = ""
    # attachment preferred
    if ctx.message.attachments:
        try:
            att = ctx.message.attachments[0]
            raw = await att.read()
            text = raw.decode("utf-8", errors="ignore")
        except Exception as e:
            return await ctx.send(f"Failed to read attachment: {e}")
    else:
        if not pasted:
            return await ctx.send("No data provided. Attach file or paste lines after command.")
        text = pasted
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    added = 0
    errors = []
    for i, line in enumerate(lines):
        # CSV or space-separated
        if "," in line:
            parts = [p.strip() for p in line.split(",", 1)]
        else:
            parts = line.split(None, 1)
        if len(parts) < 2:
            errors.append((i+1, "missing password"))
            continue
        email = parts[0].strip()
        password = parts[1].strip()
        data["generators"][key].setdefault("accounts", []).append({"email": email, "password": password})
        added += 1
    save_data(data)
    msg = f"Bulk add complete. Added {added} accounts to `{key}`."
    if errors:
        msg += " Some lines failed: " + ", ".join([f"line{ln}:{why}" for ln, why in errors])
    await ctx.send(msg)

# admin create/delete gens and set phrase
@gcart_group.command(name="creategen")
async def create_gen(ctx, generator: str, tier: str = "free"):
    if not require_admin(ctx):
        return await ctx.send("❌ Permission denied.")
    t = tier.lower()
    if t not in ("free", "vip", "booster"):
        return await ctx.send("Tier must be: free, vip, booster")
    key = norm(generator)
    if key in data["generators"]:
        return await ctx.send("Generator already exists.")
    data["generators"][key] = {"tier": t, "accounts": []}
    save_data(data)
    await ctx.send(f"✅ Created generator `{key}` (tier: {t}).")

@gcart_group.command(name="deletegen")
async def delete_gen(ctx, generator: str):
    if not require_admin(ctx):
        return await ctx.send("❌ Permission denied.")
    key = norm(generator)
    if key not in data["generators"]:
        return await ctx.send("Not found.")
    del data["generators"][key]
    save_data(data)
    await ctx.send(f"✅ Deleted `{key}`")

@gcart_group.command(name="setstatusphrase")
async def set_status_phrase(ctx, *, phrase: str):
    if not require_admin(ctx):
        return await ctx.send("❌ Permission denied.")
    data["required_status_phrase"] = phrase
    save_data(data)
    await ctx.send(f"✅ Status phrase updated to: `{phrase}`")

# debug: show detected presence info in DM
@bot.command(name="debugstatus")
async def debug_status(ctx):
    acts = getattr(ctx.author, "activities", []) or []
    if not acts:
        await ctx.author.send("No activities / presence detected.")
        return
    lines = []
    for a in acts:
        lines.append(f"repr: {repr(a)}\n state={getattr(a,'state',None)} name={getattr(a,'name',None)}")
    await ctx.author.send("```\n" + "\n\n".join(lines) + "\n```")
    await ctx.send("I DMed you presence info.")

# on_ready
@bot.event
async def on_ready():
    print(f"BOT ready: {bot.user} (id: {bot.user.id})")

# run
if __name__ == "__main__":
    token = os.getenv(TOKEN_ENV_NAME)
    if not token:
        print("ERROR: TOKEN env var missing. Set TOKEN in Railway variables.")
    else:
        bot.run(token)
