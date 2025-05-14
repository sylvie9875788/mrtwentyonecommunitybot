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
    level = 0
    while xp >= (level + 1) ** 2 * 10:
        level += 1
    return level

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

import random
from datetime import datetime
import json
import os

money_file = "money_data.json"
purchase_file = "purchases.json"
daily_file = "daily_data.json"

money_data = {}
user_purchases = {}
daily_data = {}

# Lade vorhandene Daten
if os.path.exists(money_file):
    with open(money_file, "r") as f:
        money_data = json.load(f)

if os.path.exists(purchase_file):
    with open(purchase_file, "r") as f:
        user_purchases = json.load(f)

if os.path.exists(daily_file):
    with open(daily_file, "r") as f:
        daily_data = json.load(f)

def save_money():
    with open(money_file, "w") as f:
        json.dump(money_data, f)

def save_purchases():
    with open(purchase_file, "w") as f:
        json.dump(user_purchases, f)

def save_daily():
    with open(daily_file, "w") as f:
        json.dump(daily_data, f)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    
    # Coins für Nachrichten
    money_data[user_id] = money_data.get(user_id, 0) + random.randint(3, 6)

    # XP weiterhin vergeben
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

    # 2 % Bonuschance
    if random.randint(1, 100) <= 2:
        bonus = random.randint(50, 100)
        money_data[user_id] += bonus
        await message.channel.send(f"{message.author.mention} hat einen Schatz gefunden: **{bonus} Bonus-Coins!**")

    save_money()
    save_xp()

    await bot.process_commands(message)

@bot.command()
async def konto(ctx):
    user_id = str(ctx.author.id)
    coins = money_data.get(user_id, 0)
    await ctx.send(f"{ctx.author.mention}, du hast aktuell **{coins} Coins**.")

@bot.command()
async def daily(ctx):
    user_id = str(ctx.author.id)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if daily_data.get(user_id) == today:
        await ctx.send(f"{ctx.author.mention}, du hast deine tägliche Belohnung heute schon abgeholt.")
        return

    reward = random.randint(100, 200)
    money_data[user_id] = money_data.get(user_id, 0) + reward
    daily_data[user_id] = today
    save_money()
    save_daily()
    await ctx.send(f"{ctx.author.mention}, du hast deine tägliche Belohnung erhalten: **{reward} Coins!**")

@bot.command()
async def meinekaeufe(ctx):
    user_id = str(ctx.author.id)
    history = user_purchases.get(user_id, [])
    if not history:
        await ctx.send(f"{ctx.author.mention}, du hast noch keine Käufe.")
    else:
        msg = f"**Deine letzten Käufe:**\n"
        for eintrag in history[-10:]:
            msg += f"- {eintrag}\n"
        await ctx.send(msg)
@bot.command()
async def shop(ctx):
    items = {
        "trinken": 100,
        "einhand": 500,
        "keinitem": 1000,
        "invertiert": 750,
        "augenzu": 1200,
        "ducktanz": 2500,
        "pause": 200,
        "flüstern": 600,
        "eigenlob": 150,
        "lachflash": 400
    }

    beschreibungen = {
        "trinken": "Streamer muss etwas trinken",
        "einhand": "1 Minute mit nur einer Hand spielen",
        "keinitem": "5 Minuten keine Items nutzen",
        "invertiert": "Runde mit invertierter Steuerung",
        "augenzu": "10 Sekunden mit geschlossenen Augen spielen",
        "ducktanz": "Peinlicher Ententanz im Stuhl",
        "pause": "30 Sekunden Bewegungspause",
        "flüstern": "2 Minuten nur flüstern",
        "eigenlob": "Streamer muss sich selbst loben",
        "lachflash": "30 Sekunden nur lachen"
    }

    msg = "**Shop – Verwende `!kauf <item>`**\n"
    for name, preis in items.items():
        beschr = beschreibungen[name]
        msg += f"- `{name}` ({preis} Coins): {beschr}\n"
    await ctx.send(msg)

@bot.command()
async def kauf(ctx, item: str):
    user_id = str(ctx.author.id)
    coins = money_data.get(user_id, 0)
    items = {
        "trinken": (100, "Streamer muss etwas trinken!"),
        "einhand": (500, "Streamer spielt 1 Minute nur mit einer Hand!"),
        "keinitem": (1000, "Streamer darf 5 Minuten keine Items nutzen!"),
        "invertiert": (750, "Streamer muss eine Runde invertiert spielen!"),
        "augenzu": (1200, "10 Sekunden Augen zu!"),
        "ducktanz": (2500, "Ententanz incoming!"),
        "pause": (200, "Streamer darf sich 30 Sekunden nicht bewegen!"),
        "flüstern": (600, "2 Minuten nur flüstern!"),
        "eigenlob": (150, "Streamer muss sich selbst loben!"),
        "lachflash": (400, "Streamer darf nur noch lachen!")
    }

    if item not in items:
        await ctx.send("Dieses Item gibt es nicht im Shop.")
        return

    preis, beschreibung = items[item]
    if coins < preis:
        await ctx.send(f"{ctx.author.mention}, du hast nicht genug Coins ({coins}/{preis}).")
        return

    money_data[user_id] -= preis
    user_purchases.setdefault(user_id, []).append(f"{item} – {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    save_money()
    save_purchases()
    await ctx.send(f"{ctx.author.mention} hat gekauft: **{beschreibung}**")

@bot.command()
async def blackjack(ctx):
    user_id = str(ctx.author.id)
    coins = money_data.get(user_id, 0)
    einsatz = 50
    if coins < einsatz:
        await ctx.send("Du brauchst mindestens 50 Coins zum Spielen!")
        return

    def draw():
        return random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 11])

    spieler = [draw(), draw()]
    bot_hand = [draw(), draw()]
    await ctx.send(f"Deine Karten: {spieler} (Summe: {sum(spieler)})\nDer Bot zeigt: [{bot_hand[0]}, ?]")

    while sum(spieler) < 17:
        spieler.append(draw())
    while sum(bot_hand) < 17:
        bot_hand.append(draw())

    s_sum = sum(spieler)
    b_sum = sum(bot_hand)

    result = ""
    if s_sum > 21:
        result = "Verloren – du hast dich überkauft!"
        money_data[user_id] -= einsatz
    elif b_sum > 21 or s_sum > b_sum:
        result = "Gewonnen!"
        money_data[user_id] += einsatz
    elif s_sum == b_sum:
        result = "Unentschieden."
    else:
        result = "Verloren!"
        money_data[user_id] -= einsatz

    save_money()
    await ctx.send(f"Deine Hand: {spieler} ({s_sum})\nBot: {bot_hand} ({b_sum})\n**{result}**")
bot.run(os.environ["DISCORD_BOT_TOKEN"])
