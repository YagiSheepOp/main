# main.py (updated)
"""
Discord bot with custom embed delivery using your emojis.
"""

import os
import logging
import random
import asyncio
import discord
from discord import ActivityType, Embed
from discord.errors import Forbidden
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)

# ---------------- CONFIG ----------------
TRIGGERS = {
    "gcart gen mcfa": [
        "christiebailey93@hotmail.co.uk:Chr15t13123",
        "pedrosallesfernandes@hotmail.com:Pedro2004@"
    ],
    "gcart gen stock": [
        "20+ "
    ],
}

DELIVERY_MODE = {
    "gcart gen mcfa": "dm",
    "gcart gen stock": "channel",
}

DISTRIBUTION_MODE = {
    "gcart gen mcfa": "random_repeat",
    "gcart gen stock": "round_robin",
}

STOCK_MESSAGES = {
    "gcart gen stock": "{command} — {remaining} stock remaining"
}

REQUIRED_STATUS = ".gg/CNFyBV5VnG Best Mcfa Gen"

# Custom emojis (as you provided)
EMOJI_BOOK      = "<a:400125purplebook:1447592335012532334>"
EMOJI_ARROW     = "<a:arrow_blueright:1434864844405735424>"
EMOJI_MINECRAFT = "<a:MinecraftAnimated:1390248064207552573>"

DM_TITLE = "GCART DILEVERY UNDER 1 SECOND"   # user requested title exactly
DM_FOOTER = "If it doesn't work, tell admin."

COOLDOWN_SECONDS = 60
IGNORE_CASE = True
NOTIFY_IN_CHANNEL_ON_FAIL = True
# -----------------------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

client = discord.Client(intents=intents)

cooldowns = {}
file_locks = {}
round_robin_indices = {}

def normalize(s: str) -> str:
    return s.strip().lower() if IGNORE_CASE and isinstance(s, str) else (s.strip() if isinstance(s, str) else s)

def get_lock(key: str) -> asyncio.Lock:
    lock = file_locks.get(key)
    if lock is None:
        lock = asyncio.Lock()
        file_locks[key] = lock
    return lock

async def load_file_lines(path: str):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [ln.rstrip("\n") for ln in f.readlines() if ln.strip()]

async def write_file_lines_atomic(path: str, lines: list):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    os.replace(tmp, path)

async def pick_account(source, distribution_mode: str, remove_on_deliver: bool):
    if isinstance(source, list):
        key = f"__list_{id(source)}"
        lock = get_lock(key)
        async with lock:
            if not source:
                return None
            if distribution_mode == "consume":
                choice = random.choice(source)
                if remove_on_deliver:
                    try:
                        source.remove(choice)
                    except ValueError:
                        pass
                return choice
            elif distribution_mode == "random_repeat":
                return random.choice(source)
            elif distribution_mode == "round_robin":
                idx = round_robin_indices.get(key, 0)
                choice = source[idx % len(source)]
                round_robin_indices[key] = (idx + 1) % len(source)
                return choice
            else:
                return random.choice(source)

    if isinstance(source, str):
        filename = source
        path = os.path.join(os.path.dirname(__file__), filename)
        lock = get_lock(path)
        async with lock:
            lines = await load_file_lines(path)
            if not lines:
                return None
            if distribution_mode == "consume":
                choice = random.choice(lines)
                if remove_on_deliver:
                    removed = False
                    new_lines = []
                    for ln in lines:
                        if (not removed) and ln == choice:
                            removed = True
                            continue
                        new_lines.append(ln)
                    await write_file_lines_atomic(path, new_lines)
                return choice
            elif distribution_mode == "random_repeat":
                return random.choice(lines)
            elif distribution_mode == "round_robin":
                key = path
                idx = round_robin_indices.get(key, 0)
                choice = lines[idx % len(lines)]
                round_robin_indices[key] = (idx + 1) % len(lines)
                return choice
            else:
                return random.choice(lines)
    return None

def get_remaining(source) -> int:
    if isinstance(source, list):
        return len(source)
    if isinstance(source, str):
        path = os.path.join(os.path.dirname(__file__), source)
        if not os.path.exists(path):
            return 0
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for ln in f.readlines() if ln.strip())
    return 0

def user_has_required_status(member: discord.Member) -> bool:
    if not member:
        return False
    acts = getattr(member, "activities", None)
    if not acts:
        return False
    for act in acts:
        try:
            if getattr(act, "type", None) == ActivityType.custom:
                state = getattr(act, "state", None) or ""
                if not state:
                    continue
                if IGNORE_CASE:
                    if REQUIRED_STATUS.lower() in state.lower():
                        return True
                else:
                    if REQUIRED_STATUS in state:
                        return True
        except Exception:
            continue
    return False

def on_cooldown(user_id: int, command: str) -> (bool, float):
    key = (user_id, normalize(command))
    next_allowed = cooldowns.get(key)
    now = datetime.utcnow()
    if next_allowed and next_allowed > now:
        return True, (next_allowed - now).total_seconds()
    return False, 0.0

def set_cooldown(user_id: int, command: str, seconds: int):
    key = (user_id, normalize(command))
    cooldowns[key] = datetime.utcnow() + timedelta(seconds=seconds)

# --------- NEW: custom embed builder & sender ----------
def build_custom_embed(user: discord.abc.Snowflake, command: str, account: str) -> Embed:
    """
    Build embed using the three custom emojis and the layout you requested.
    Email -- >> <email>
    Password -->> <password>
    Footer instructs to tell admin if it doesn't work.
    No timestamp.
    """
    # parse account into email/password
    email = account
    password = ""
    if isinstance(account, str) and ":" in account:
        # split only on first colon to allow colons in password
        parts = account.split(":", 1)
        email = parts[0].strip()
        password = parts[1].strip()
    else:
        # keep entire account in email field if no separator
        email = account.strip()

    title = f"{EMOJI_BOOK}  {DM_TITLE}"
    embed = Embed(title=title, description=f"{EMOJI_ARROW}  **Your requested account is below**", color=0x6A3BE2)
    # Email and password fields using exactly the text layout requested
    embed.add_field(name="Email -- >>", value=f"`{email}`", inline=False)
    if password:
        embed.add_field(name="Password -->>", value=f"`{password}`", inline=False)
    else:
        embed.add_field(name="Password -->>", value="`(none)`", inline=False)

    # short status field with the minecraft emoji
    embed.add_field(name=f"{EMOJI_MINECRAFT} Status", value="Delivered — if it doesn't work tell admin.", inline=False)

    # footer (no timestamp)
    display = getattr(user, "display_name", getattr(user, "name", str(user)))
    embed.set_footer(text=f"Requested by {display} • GCart")
    return embed

async def send_custom_delivery(target, user, command: str, account: str):
    """
    target: discord.User/Member (for DM) or a TextChannel (for public).
    user: the requester Member/User for footer and mention.
    """
    embed = build_custom_embed(user, command, account)
    try:
        if isinstance(target, (discord.User, discord.Member)):
            await target.send(embed=embed)
        else:
            await target.send(content=f"{user.mention}", embed=embed)
    except Forbidden:
        # fallback notifications
        if isinstance(target, (discord.User, discord.Member)):
            # couldn't DM the user
            # We won't re-add the account here; just notify
            print("Couldn't DM user; DMs may be closed.")
        else:
            try:
                await target.send("I don't have permission to send embeds here. Please check my permissions.")
            except Exception:
                pass
    except Exception as e:
        print("Error sending custom delivery:", e)
# ------------------------------------------------------

@client.event
async def on_ready():
    logging.info(f"Logged in as {client.user} (id: {client.user.id})")
    logging.info("Bot is ready.")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if not message.guild:
        return

    content = message.content or ""
    text = normalize(content)

    for cmd_text, source in TRIGGERS.items():
        if text == normalize(cmd_text):
            user = message.author

            # required status check
            if not user_has_required_status(user):
                await message.channel.send(
                    f"{user.mention} To use this command you must add `{REQUIRED_STATUS}` to your custom status. "
                    "Set your custom status (bottom-left avatar → Set Status) and include that text."
                )
                return

            # cooldown
            on_cd, secs = on_cooldown(user.id, cmd_text)
            if on_cd:
                await message.channel.send(f"{user.mention} Please wait {int(secs)}s before using this command again.")
                return

            dist_mode = DISTRIBUTION_MODE.get(cmd_text, "random_repeat")
            remove_flag = (dist_mode == "consume")

            account = await pick_account(source, distribution_mode=dist_mode, remove_on_deliver=remove_flag)
            if not account:
                await message.channel.send(f"{user.mention} Sorry — no accounts available for `{cmd_text}`. Ask an admin.")
                return

            mode = DELIVERY_MODE.get(cmd_text, "dm")

            try:
                # use the custom embed sender for both DM and channel
                if mode == "dm":
                    await send_custom_delivery(user, user, cmd_text, account)
                    try:
                        await message.add_reaction("✅")
                    except Exception:
                        pass
                else:
                    await send_custom_delivery(message.channel, user, cmd_text, account)
                    try:
                        await message.add_reaction("✅")
                    except Exception:
                        pass

                set_cooldown(user.id, cmd_text, COOLDOWN_SECONDS)

                # If this is the stock command and we want to show remaining, send stock message (only for channel mode)
                if cmd_text in STOCK_MESSAGES:
                    remaining = get_remaining(source)
                    template = STOCK_MESSAGES.get(cmd_text)
                    if template and mode == "channel":
                        try:
                            await message.channel.send(template.format(command=cmd_text, remaining=remaining))
                        except Exception:
                            pass

            except Forbidden:
                if mode == "dm" and NOTIFY_IN_CHANNEL_ON_FAIL:
                    await message.channel.send(f"{user.mention} I couldn't DM you — please enable DMs from server members.")
                elif mode == "channel" and NOTIFY_IN_CHANNEL_ON_FAIL:
                    try:
                        await user.send("I couldn't post publicly in that channel (missing permissions). Please contact an admin.")
                    except Exception:
                        pass

            return

if __name__ == "__main__":
    TOKEN = os.getenv("MTQ0ODY4MzkzNjgxNjU2NjQ0Nw.GE3inB.mmVBsVO3vPFBBx2WqrfOlwagmHY-6JSHScznoI")
    if not TOKEN:
        raise SystemExit("Set DISCORD_BOT_TOKEN env var in Railway (Variables tab).")
    client.run(TOKEN)
