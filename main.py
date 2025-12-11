# bot.py
"""
Discord bot with configurable distribution modes per command:
  - "consume": remove account when delivered (used once)
  - "random_repeat": pick random but do NOT remove (accounts can be reused)
  - "round_robin": serve accounts in order, wrap around (do NOT remove)
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
# TRIGGERS: command -> filename (str) OR list of account strings
TRIGGERS = {
    "gcart gen mcfa": [
        "christiebailey93@hotmail.co.uk:Chr15t13123",
        "pedrosallesfernandes@hotmail.com:Pedro2004@"
    ],
    "gcart gen stock": [
        "20+ "
    ],
}

# DELIVERY_MODE: "dm" or "channel"
DELIVERY_MODE = {
    "gcart gen mcfa": "dm",
    "gcart gen stock": "channel",
}

# DISTRIBUTION_MODE per command:
# - "consume"      -> remove account after delivering (one-time use)
# - "random_repeat"-> random pick but DO NOT remove (accounts reused)
# - "round_robin"  -> cycle through accounts in order (reused, orderly)
DISTRIBUTION_MODE = {
    "gcart gen mcfa": "random_repeat",   # give same pool repeatedly (random)
    "gcart gen stock": "round_robin",    # cycle accounts in order for each request
}

# STOCK_MESSAGES only relevant for stock command (you can change wording)
STOCK_MESSAGES = {
    "gcart gen stock": "{command} — {remaining} stock remaining"
}

# Required status substring users must have in custom status
REQUIRED_STATUS = ".gg/CNFyBV5VnG Best Mcfa Gen"

DM_TITLE = "🎁 Your free account from GCart"
DM_FOOTER = "If the account doesn't work, try another or contact admin."

COOLDOWN_SECONDS = 60       # cooldown per user per command
IGNORE_CASE = True
NOTIFY_IN_CHANNEL_ON_FAIL = True
# -----------------------------------------

# Intents - ensure these are toggled in Developer Portal
intents = discord.Intents.default()
intents.message_content = True
intents.presences = True   # required to read custom status
intents.members = True

client = discord.Client(intents=intents)

# runtime state
cooldowns = {}            # (user_id, cmd) -> datetime
file_locks = {}           # key -> asyncio.Lock
round_robin_indices = {}  # key (id(source) or path) -> next index (int)

def normalize(s: str) -> str:
    return s.strip().lower() if IGNORE_CASE and isinstance(s, str) else (s.strip() if isinstance(s, str) else s)

def get_lock(key: str) -> asyncio.Lock:
    lock = file_locks.get(key)
    if lock is None:
        lock = asyncio.Lock()
        file_locks[key] = lock
    return lock

async def load_file_lines(path: str):
    """Read non-empty lines from file, return list of strings (or [] if missing/empty)."""
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
    """
    source: either a list or a filename (string).
    distribution_mode: "consume", "random_repeat", "round_robin"
    remove_on_deliver: if True and distribution_mode == "consume", remove the delivered item
    Returns chosen account string or None.
    """
    # In-memory list case
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
                # advance index
                round_robin_indices[key] = (idx + 1) % len(source)
                return choice

            else:
                # unknown mode -> fallback to random_repeat
                return random.choice(source)

    # File-backed case
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
                    # remove first matching line
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
    """Return remaining count (lines or list length). For consume mode this reflects current pool."""
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
    """Check member.activities for a custom status containing REQUIRED_STATUS."""
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

            # decide distribution mode for this command
            dist_mode = DISTRIBUTION_MODE.get(cmd_text, "random_repeat")
            # remove_on_deliver should only be True if using "consume"
            remove_flag = (dist_mode == "consume")

            # pick account
            account = await pick_account(source, distribution_mode=dist_mode, remove_on_deliver=remove_flag)
            if not account:
                await message.channel.send(f"{user.mention} Sorry — no accounts available for `{cmd_text}`. Ask an admin.")
                return

            # build embed
            embed = Embed(title=DM_TITLE, description=f"**Command:** {cmd_text}", color=0x2ecc71)
            embed.add_field(name="Account", value=f"```{account}```", inline=False)
            embed.set_footer(text=DM_FOOTER)
            try:
                embed.timestamp = datetime.utcnow()
            except Exception:
                pass

            mode = DELIVERY_MODE.get(cmd_text, "dm")

            try:
                if mode == "dm":
                    await user.send(embed=embed)
                    try:
                        await message.add_reaction("✅")
                    except Exception:
                        pass
                else:
                    public_embed = Embed(title=DM_TITLE, description=f"**Command:** {cmd_text}", color=0x2ecc71)
                    public_embed.add_field(name="Account", value=f"```{account}```", inline=False)
                    public_embed.set_footer(text=DM_FOOTER)
                    try:
                        public_embed.timestamp = datetime.utcnow()
                    except Exception:
                        pass
                    await message.channel.send(content=f"{user.mention}", embed=public_embed)
                    try:
                        await message.add_reaction("✅")
                    except Exception:
                        pass

                set_cooldown(user.id, cmd_text, COOLDOWN_SECONDS)

                # Only send stock message for commands listed in STOCK_MESSAGES and only when it's public (you can change)
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
    TOKEN = os.getenv("DISCORD_BOT_TOKEN", "MTQ0ODY4MzkzNjgxNjU2NjQ0Nw.G0YnD3.JCaK6cPQSwat6pF1vQXoYFyTM7hhH8VnIKJcfk")
    if not TOKEN or TOKEN == "PASTE_YOUR_TOKEN_HERE":
        raise SystemExit("Set DISCORD_BOT_TOKEN env var or replace the placeholder in the script.")
    client.run(TOKEN)
