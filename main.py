import os
import discord
from discord.ext import commands, tasks
import aiohttp
import json

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

TWITCH_CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")
TWITCH_USER_LOGIN = "MrTwentyOne7"
TWITCH_LINK = "https://twitch.tv/MrTwentyOne7"
TIKTOK_LINK = "https://tiktok.com/@mr_twentyy_onee"
LIVE_CHANNEL_NAME = "🔴・wer-ist-live"
XP_FILE = "xp_data.json"

access_token = None
xp_data = {}

LEVEL_ROLES = {
    i: f"Level {i} – {text}" for i, text in {
        1: "Frisch aus dem Ei",
        2: "Discord-Tourist",
        3: "Chat-Schnupperer",
        4: "Reaktionsjäger",
        5: "GIF-Gott in Ausbildung",
        6: "Emoji-Forscher",
        7: "Sprachkanal-Vermeider",
        8: "Memelord-Lehrling",
        9: "Sticker-Spammer",
        10: "Teilzeit-Kommentator",
        11: "Laberanfänger",
        12: "Sarkasmus-Schleuder",
        13: "Achtet nie auf Regeln",
        14: "Textwand-Baumeister",
        15: "Channel-Ninja",
        16: "Rollenjäger",
        17: "Voice-Lurker",
        18: "Kaffee-trinkender Chiller",
        19: "Spam-Philosoph",
        20: "Kommt immer zu spät",
        21: "Chronischer Discord-User",
        22: "Meme-Wissenschaftler",
        23: "Ironie-Experte",
        24: "Afk-Profi",
        25: "Fast Legende",
        26: "Kanal-Kommandant",
        27: "Reaktions-König",
        28: "Viel zu aktiv",
        29: "Kann nicht aufhören",
        30: "LEGENDE"
    }.items()
}

if os.path.exists(XP_FILE):
    with open(XP_FILE, "r") as f:
        xp_data = json.load(f)

def save_xp():
    with open(XP_FILE, "w") as f:
        json.dump(xp_data, f)

def get_level(xp):
    return int(xp ** 0.5)

@bot.event
async def on_ready():
    print(f"Bot ist online als {bot.user}")
    await get_twitch_access_token()
    check_twitch_live.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    user_id = str(message.author.id)
    xp_data[user_id] = xp_data.get(user_id, 0) + 5
    level_before = get_level(xp_data[user_id] - 5)
    level_now = get_level(xp_data[user_id])
    if level_now > level_before:
        await message.channel.send(f"{message.author.mention} hat Level {level_now} erreicht!")
        if level_now in LEVEL_ROLES:
            role_name = LEVEL_ROLES[level_now]
            role = discord.utils.get(message.guild.roles, name=role_name)
            if not role:
                role = await message.guild.create_role(name=role_name)
            await message.author.add_roles(role)
            await message.channel.send(f"{message.author.mention} hat die Rolle **{role.name}** erhalten!")
    save_xp()
    await bot.process_commands(message)
    @bot.command()
async def level(ctx):
    user_id = str(ctx.author.id)
    xp = xp_data.get(user_id, 0)
    level = get_level(xp)
    await ctx.send(f"{ctx.author.mention}, du hast **{xp} XP** und bist Level **{level}**.")

@bot.command()
async def rangliste(ctx):
    top = sorted(xp_data.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "**Top 10 Spieler:**\n"
    for i, (user_id, xp) in enumerate(top, 1):
        member = await ctx.guild.fetch_member(int(user_id))
        text += f"{i}. {member.display_name} – {xp} XP\n"
    await ctx.send(text)

@bot.command()
@commands.has_any_role("Admin", "Moderator", "Streamer")
async def live(ctx):
    await ctx.send(f"**MrTwentyOne7 ist LIVE unterwegs!**\nTwitch: {TWITCH_LINK}\nTikTok: {TIKTOK_LINK}")

@bot.command()
@commands.has_any_role("Admin", "Moderator", "Streamer")
async def live10(ctx):
    channel = discord.utils.get(ctx.guild.text_channels, name=LIVE_CHANNEL_NAME)
    if channel:
        msg = "**Live in 10 Minuten! Kommt rein, lasst uns spielen und quatschen!**"
        await channel.send(msg)
    else:
        await ctx.send(f"Kanal '{LIVE_CHANNEL_NAME}' wurde nicht gefunden.")

@bot.command()
@commands.has_any_role("Admin", "Moderator", "Streamer")
async def setup(ctx):
    guild = ctx.guild
    base_roles = ["Admin", "Moderator", "Streamer", "Mitglied", "GamingNow"]
    roles = {}
    for role_name in base_roles:
        role = await guild.create_role(name=role_name)
        roles[role_name.lower()] = role

    categories = {
        "INFO": ["📢・ankündigungen", "✅・regeln"],
        "COMMUNITY": ["💬・allgemein", "🖼️・memes-und-bilder", "🤖・bot-befehle"],
        "STREAMING": ["🎥・live-streams", "🗓️・stream-plan", "🔴・wer-ist-live"],
        "SUPPORT": ["❓・hilfe-und-feedback", "🎫・ticket-system"],
        "SPRECHZIMMER": []
    }

    for category_name, channels in categories.items():
        category = await guild.create_category(category_name)
        for channel_name in channels:
            await guild.create_text_channel(channel_name, category=category)

    sprech_category = discord.utils.get(guild.categories, name="SPRECHZIMMER")
    await guild.create_voice_channel("⏳・warteraum", category=sprech_category)

    overwrites_live = {
        guild.default_role: discord.PermissionOverwrite(connect=False),
        roles["gamingnow"]: discord.PermissionOverwrite(connect=True),
        roles["moderator"]: discord.PermissionOverwrite(connect=True),
        roles["admin"]: discord.PermissionOverwrite(connect=True),
    }
    await guild.create_voice_channel("🎮・live-gaming", category=sprech_category, overwrites=overwrites_live)

    overwrites_mod = {
        guild.default_role: discord.PermissionOverwrite(connect=False),
        roles["moderator"]: discord.PermissionOverwrite(connect=True),
        roles["admin"]: discord.PermissionOverwrite(connect=True),
    }
    await guild.create_voice_channel("🛠️・mod-room", category=sprech_category, overwrites=overwrites_mod)

    for lvl, role_name in LEVEL_ROLES.items():
        await guild.create_role(name=role_name)

    await ctx.send("Setup abgeschlossen! Alle Räume, Rollen und Levelrollen wurden erstellt.")

# Fehlerbehandlung für fehlende Rechte
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("Du hast keine Berechtigung für diesen Befehl.")
    else:
        raise error

# Twitch-Token holen
async def get_twitch_access_token():
    global access_token
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as resp:
            data = await resp.json()
            access_token = data.get("access_token")

# Twitch-Live-Check
@tasks.loop(seconds=60)
async def check_twitch_live():
    global access_token
    if not access_token:
        await get_twitch_access_token()

    url = f"https://api.twitch.tv/helix/streams?user_login={TWITCH_USER_LOGIN}"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            if data.get("data"):
                stream = data["data"][0]
                if stream["type"] == "live":
                    for guild in bot.guilds:
                        channel = discord.utils.get(guild.text_channels, name=LIVE_CHANNEL_NAME)
                        if channel:
                            if not hasattr(bot, "last_stream_id") or bot.last_stream_id != stream["id"]:
                                bot.last_stream_id = stream["id"]
                                msg = f"**{TWITCH_USER_LOGIN} ist jetzt live auf Twitch!**\n{TWITCH_LINK}"
                                await channel.send(msg)

bot.run(os.environ["DISCORD_BOT_TOKEN"])
