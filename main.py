import discord
from discord.ext import commands
import os
import json

intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!gcart ", intents=intents)

# ---------------- LOAD DATA ---------------- #
with open("data.json", "r") as f:
    DATA = json.load(f)

REQUIRED_STATUS = DATA["required_status"].lower()


# ---------------- STATUS CHECK ---------------- #
def has_required_status(member):
    try:
        if member.activity and member.activity.state:
            status_text = str(member.activity.state).lower()
            return REQUIRED_STATUS in status_text
        return False
    except:
        return False


# ---------------- STATUS ERROR EMBED ---------------- #
async def send_status_error(ctx):
    embed = discord.Embed(
        title="❌ Required Status Missing",
        description=f"""
<a:animatedarrowgreen:1450811653552607296> Use This Status to Access Gen System:

