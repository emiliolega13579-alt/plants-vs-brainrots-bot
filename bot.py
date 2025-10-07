import os
import json
from typing import List
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
SHOP_CHANNEL_ID = int(os.getenv("SHOP_CHANNEL_ID", "0"))
ALERT_ROLE_ID = int(os.getenv("ALERT_ROLE_ID", "0"))
ITEMS = [i.strip().lower() for i in os.getenv("ITEMS", "mango,fruta mango,mango fruit").split(",")]
STATE_FILE = "state.json"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"notified_message_ids": []}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)

state = load_state()

def find_items_in_text(text: str) -> List[str]:
    text = text.lower()
    return [item for item in ITEMS if item in text]

async def notify_channel(channel: discord.TextChannel, matches: List[str]):
    guild = channel.guild
    role = guild.get_role(ALERT_ROLE_ID)
    mention = role.mention if role else f"<@&{ALERT_ROLE_ID}>"
    await channel.send(f"{mention} ¡Tienda actualizada! Encontré: {', '.join(matches)}")

@bot.event
async def on_ready():
    print(f"✅ Conectado como {bot.user} (id: {bot.user.id})")

@bot.event
async def on_message(message: discord.Message):
    try:
        if message.channel and message.channel.id == SHOP_CHANNEL_ID:
            parts = [message.content or ""]
            for emb in message.embeds:
                if emb.title:
                    parts.append(str(emb.title))
                if emb.description:
                    parts.append(str(emb.description))
                for f in getattr(emb, "fields", []):
                    parts.append(str(f.name))
                    parts.append(str(f.value))
            full = "\n".join(parts)
            matches = find_items_in_text(full)
            if matches and str(message.id) not in state["notified_message_ids"]:
                await notify_channel(message.channel, matches)
                state["notified_message_ids"].append(str(message.id))
                state["notified_message_ids"] = state["notified_message_ids"][-300:]
                save_state(state)
    except Exception as e:
        print("Error on_message:", e)
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    try:
        if after.channel and after.channel.id == SHOP_CHANNEL_ID:
            parts = [after.content or ""]
            for emb in after.embeds:
                if emb.title:
                    parts.append(str(emb.title))
                if emb.description:
                    parts.append(str(emb.description))
                for f in getattr(emb, "fields", []):
                    parts.append(str(f.name))
                    parts.append(str(f.value))
            full = "\n".join(parts)
            matches = find_items_in_text(full)
            if matches and str(after.id) not in state["notified_message_ids"]:
                await notify_channel(after.channel, matches)
                state["notified_message_ids"].append(str(after.id))
                state["notified_message_ids"] = state["notified_message_ids"][-300:]
                save_state(state)
    except Exception as e:
        print("Error on_message_edit:", e)

if __name__ == "__main__":
    if not TOKEN or SHOP_CHANNEL_ID == 0 or ALERT_ROLE_ID == 0:
        print("Faltan variables de entorno. Revisa DISCORD_TOKEN, SHOP_CHANNEL_ID, ALERT_ROLE_ID.")
    else:
        bot.run(TOKEN)
