import discord
from discord.ext import commands
import json
import os

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

XP_PER_MESSAGE = 5
LEVELS = {i: {"name": f"Level {i}", "quote": quote} for i, quote in {
    1: "Gerade erst gespawnt und schon am Quatschen.",
    2: "Zwei Level und noch kein Plan.",
    3: "Level 3 – denkt, sie wissen was.",
    4: "Kaffee ist noch kein Talent, aber du bist auf dem Weg!",
    5: "Schon fünf? Irgendwer redet zu viel.",
    6: "Fast ein Profi im Nichtstun.",
    7: "Gehst du auch mal raus?",
    8: "Redet mehr als der Bot.",
    9: "Bald braucht’s ein Maulkorb.",
    10: "Level 10: Halb Mensch, halb Tastatur.",
    11: "Könnte bald Moderator spielen (aber nur spielen).",
    12: "Level 12 und immer noch keine Ahnung.",
    13: "Freitag der 13., passend.",
    14: "Das Level der seltsamen Memes.",
    15: "Halbzeit zum Endgegner der Peinlichkeit.",
    16: "Jetzt wird's langsam ernst. Oder auch nicht.",
    17: "Level 17 – klingt wichtiger als es ist.",
    18: "Endlich volljährig im Botland.",
    19: "Kurz vor dem Nerdorden.",
    20: "Du bist der Chat-Boss. Aber nur für heute.",
    21: "Stolzer Besitzer von 21 nutzlosen Leveln.",
    22: "Niemand mag Level 22. Außer du.",
    23: "Redest du noch oder tippst du schon im Schlaf?",
    24: "Bot fragt schon, ob du Mitarbeiter bist.",
    25: "Viertelhundert. Fast Ehrenmitglied.",
    26: "Wissen wir überhaupt, dass du existierst?",
    27: "27 – Das Level der Ironie.",
    28: "Fast oben. Niemand weiß warum.",
    29: "Was kommt jetzt noch? Kuchen?",
    30: "Du hast es geschafft. Glückwunsch, oder so."
}.items()}

LEVELS_FILE = "level.json"

if not os.path.exists(LEVELS_FILE):
    with open(LEVELS_FILE, "w") as f:
        json.dump({}, f)

def get_user_data():
    with open(LEVELS_FILE, "r") as f:
        return json.load(f)

def save_user_data(data):
    with open(LEVELS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_level(xp):
    return xp // 100 + 1

@bot.event
async def on_ready():
    print(f"{bot.user} ist online.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    data = get_user_data()
    user_id = str(message.author.id)
    xp = data.get(user_id, 0) + XP_PER_MESSAGE
    level = get_level(xp)
    old_level = get_level(data.get(user_id, 0))
    data[user_id] = xp
    save_user_data(data)

    if level > old_level and level <= 30:
        role_name = LEVELS[level]["name"]
        quote = LEVELS[level]["quote"]
        guild = message.guild
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            role = await guild.create_role(name=role_name)
        await message.author.add_roles(role)
        await message.channel.send(f"{message.author.mention} hat {role_name} erreicht! {quote}")

    await bot.process_commands(message)

@bot.command()
async def lvl(ctx):
    data = get_user_data()
    xp = data.get(str(ctx.author.id), 0)
    level = get_level(xp)
    await ctx.send(f"{ctx.author.mention}, du bist Level {level} mit {xp} XP.")

@bot.command()
async def rangliste(ctx):
    data = get_user_data()
    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)
    text = ""
    for i, (user_id, xp) in enumerate(sorted_users[:10], 1):
        member = await ctx.guild.fetch_member(int(user_id))
        text += f"{i}. {member.display_name} – {get_level(xp)} ({xp} XP)
"
    await ctx.send("**Rangliste der aktivsten Mitglieder:**
" + text)

bot.run(os.getenv("DISCORD_TOKEN"))
