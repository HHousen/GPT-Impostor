import os
import logging
import sqlalchemy as db
from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database
from discord import Client, Intents
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
from helpers import run_gpt_inference, get_gpt_first_message
from models import Guild, User, Statistic, Base

try:
    RUNNING_IN_REPLIT = os.environ["RUNNING_IN_REPLIT"]
except KeyError:
    RUNNING_IN_REPLIT = False
if RUNNING_IN_REPLIT:
    from keep_alive import keep_alive

discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.DEBUG)
discord_handler = logging.FileHandler(
    filename="log_db/discord.log", encoding="utf-8", mode="a+"
)
discord_handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
discord_logger.addHandler(discord_handler)

gpt_logger = logging.getLogger("gpt")
gpt_logger.setLevel(logging.DEBUG)
gpt_handler = logging.FileHandler(
    filename="log_db/gpt.log", encoding="utf-8", mode="a+"
)
gpt_handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
gpt_logger.addHandler(gpt_handler)


BOT_TOKEN = os.environ["BOT_TOKEN"]
MESSAGE_CONTEXT_LIMIT = 50  # Max number of messages to send as context to AI model
ALLOW_BOT_MESSAGES_IN_CONTEXT = True
GPT_INVALID_RESPONSE_MESSAGE = (
    "Sorry, I could not think of a good message. Please make "
    + "sure there are enough messages in this channel so that I can learn how you write."
)

bot = Client(intents=Intents.default())
slash = SlashCommand(bot, sync_commands=True)
engine = db.create_engine(os.environ["DATABASE_URL"])
if not database_exists(engine.url):
    create_database(engine.url)
Base.metadata.create_all(engine)


@bot.event
async def on_ready():
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.author.bot:
        return

    if not message.mentions:
        return

    if bot.user in message.mentions:
        webhook, first_response_message = await gpt_channel_response(
            message.channel, bot.user
        )
        if first_response_message:
            await message.channel.send(first_response_message)

    with Session(engine) as session:
        guild_db = session.query(Guild).filter(Guild.id == message.guild.id).first()
        guild_ping_mode_users = None
        if guild_db:
            guild_ping_mode_users = guild_db.ping_mode_users

    if guild_ping_mode_users:
        can_be_impersonated = {x.id for x in guild_ping_mode_users}
        message_mentions_ids = {x.id: x for x in message.mentions}
        user_ids_to_impersonate = can_be_impersonated.intersection(
            set(message_mentions_ids.keys())
        )
        for user_id_to_impersonate in user_ids_to_impersonate:
            user = message_mentions_ids[user_id_to_impersonate]
            webhook, first_response_message = await gpt_channel_response(
                message.channel, user
            )
            if first_response_message:
                await webhook.send(
                    first_response_message,
                    username=user.name,
                    avatar_url=user.avatar_url,
                )
                log_new_stat("Impersonation Count")


async def get_channel_webhook(channel):
    discord_logger.debug("Getting channel %s's webhook...", channel.id)
    webhooks = await channel.webhooks()
    webhook = next((x for x in webhooks if x.name == str(channel.id)), False)
    if not webhook:
        webhook = await channel.create_webhook(name=channel.id)
    return webhook


async def get_previous_messages(channel, as_string=True):
    discord_logger.debug("Getting channel %s's previous messages...", channel.id)
    previous_messages = await channel.history(limit=MESSAGE_CONTEXT_LIMIT).flatten()
    if not ALLOW_BOT_MESSAGES_IN_CONTEXT:
        previous_messages = [
            message for message in previous_messages if not message.author.bot
        ]
    # Messages are retrieved so newest are first but GPT should read them as a
    # normal conversation.
    previous_messages.reverse()
    if as_string:
        previous_messages_str = "\n".join(
            [
                f"{message.author.name}: {message.content}"
                for message in previous_messages
            ]
        )
        return previous_messages_str
    else:
        return previous_messages


def log_new_stat(stat_name, increment_count=1):
    with Session(engine) as session:
        stat = session.query(Statistic).filter(Statistic.name == stat_name).first()
        if not stat:
            stat = Statistic(name=stat_name, value=0)

        stat.value += increment_count

        session.add(stat)
        session.commit()


@slash.slash(
    name="monologue",
    description="Have AI continue your conversation (multiple messages).",
    options=[
        create_option(
            name="max_messages",
            description="The maximum number of messages to generate (default 25).",
            option_type=4,
            required=False,
        )
    ],
)
async def monologue(ctx: SlashContext, max_messages=25):
    await ctx.defer(hidden=True)

    channel = bot.get_channel(ctx.channel_id)
    webhook = await get_channel_webhook(channel)

    previous_messages_str = await get_previous_messages(channel)

    gpt_response = run_gpt_inference(previous_messages_str, token_max_length=512)
    log_new_stat("GPT Inference Calls")
    gpt_messages = [
        message.split(":", 1) for message in gpt_response.strip().split("\n")
    ]
    del gpt_messages[-1]

    gpt_messages = gpt_messages[:max_messages]

    for content in gpt_messages:
        if len(content) <= 1:
            await ctx.send(
                GPT_INVALID_RESPONSE_MESSAGE, hidden=True,
            )
            return

    log_new_stat("Impersonation Count", len(gpt_messages))
    for user, message in gpt_messages:
        if message:
            await webhook.send(message, username=user)
    await ctx.send("Fake conversation sent!", hidden=True)


@slash.slash(
    name="sus",
    description="Send a message as the specified user.",
    options=[
        create_option(
            name="user",
            description="Choose the user to impersonate.",
            option_type=6,
            required=True,
        )
    ],
)
async def sus(ctx: SlashContext, user=None):
    await ctx.defer(hidden=True)

    channel = bot.get_channel(ctx.channel_id)
    webhook, first_response_message = await gpt_channel_response(channel, user)

    if not first_response_message:
        await ctx.send(
            GPT_INVALID_RESPONSE_MESSAGE, hidden=True,
        )
    else:
        await webhook.send(
            first_response_message, username=user.name, avatar_url=user.avatar_url
        )
        await ctx.send("Fake message sent!", hidden=True)
        log_new_stat("Impersonation Count")


async def gpt_channel_response(channel, user):
    webhook = await get_channel_webhook(channel)

    previous_messages_str = await get_previous_messages(channel)

    context = previous_messages_str + f"\n{user.name}: "
    gpt_logger.debug(f"Context ({channel.id}):\n{context}\n-----------")

    gpt_response = run_gpt_inference(context, token_max_length=50)
    log_new_stat("GPT Inference Calls")
    gpt_logger.debug(f"GPT Response ({channel.id}):\n{gpt_response}\n-----------")

    first_response_message = get_gpt_first_message(gpt_response, user.name)
    return webhook, first_response_message


@slash.slash(
    name="adduser",
    description="Impersonate a specific user when they are pinged.",
    options=[
        create_option(
            name="user",
            description="Choose the user to impersonate.",
            option_type=6,
            required=True,
        )
    ],
)
async def adduser(ctx: SlashContext, user):
    if user == bot.user:
        await ctx.send(
            "You cannot impersonate me! I already respond to messages automatically. Try pinging me.",
            hidden=True,
        )
        return
    with Session(engine) as session:
        guild = session.query(Guild).filter(Guild.id == ctx.guild_id).first()
        user_db = session.query(User).filter(User.id == user.id).first()
        if user_db and guild and user_db in guild.ping_mode_users:
            await ctx.send(f"Already impersonating {user.name}.", hidden=True)
            return

        if not guild:
            guild = Guild(id=int(ctx.guild_id))
        if not user_db:
            user_db = User(id=int(user.id), name=user.name)
        guild.ping_mode_users.append(user_db)
        session.add(user_db)
        session.add(guild)
        session.commit()
    await ctx.send(f"Impersonating {user.name}.", hidden=True)


@slash.slash(
    name="deluser",
    description="Remove a user from the impersonation list so they are not longer impersonated when pinged.",
    options=[
        create_option(
            name="user",
            description="Choose the user to remove.",
            option_type=6,
            required=True,
        )
    ],
)
async def deluser(ctx: SlashContext, user):
    with Session(engine) as session:
        guild = session.query(Guild).filter(Guild.id == ctx.guild_id).first()
        user_db = session.query(User).filter(User.id == user.id).first()
        if user_db and guild and user_db in guild.ping_mode_users:
            guild.ping_mode_users.remove(user_db)
            session.delete(user_db)
            session.commit()
            await ctx.send(
                f"{user.name} will no longer being impersonated.", hidden=True
            )
        else:
            await ctx.send(
                f"{user.name} is not actively being impersonated and thus cannot be removed.",
                hidden=True,
            )


@slash.slash(
    name="list", description="List users currently being impersonated.",
)
async def impersonating_list(ctx: SlashContext):
    with Session(engine) as session:
        guild_db = session.query(Guild).filter(Guild.id == ctx.guild_id).first()
        if guild_db and guild_db.ping_mode_users:
            guild_ping_mode_users = guild_db.ping_mode_users
            impersonating_str = ", ".join(
                [x.name for x in guild_ping_mode_users]
            ).strip()
            await ctx.send(f"Currently impersonating {impersonating_str}.", hidden=True)
        else:
            await ctx.send(
                f"No one is currently being impersonated. Add someone with `/adduser`.",
                hidden=True,
            )


@slash.slash(
    name="stats", description="Get statistics about the GPT Impostor bot.",
)
async def stats(ctx: SlashContext):
    server_count = len(bot.guilds)
    member_count = len(set(bot.get_all_members()))
    with Session(engine) as session:
        gpt_inference_count = (
            session.query(Statistic)
            .filter(Statistic.name == "GPT Inference Calls")
            .first()
            .value
        )
        impersonation_count = (
            session.query(Statistic)
            .filter(Statistic.name == "Impersonation Count")
            .first()
            .value
        )
    await ctx.send(
        f"GPT Impostor is in **{server_count} servers** totaling **{member_count} members**. It has made **{gpt_inference_count} message predictions** and has sent a message impersonating someone **{impersonation_count} times**.",
        hidden=True,
    )


if RUNNING_IN_REPLIT:
    keep_alive()
bot.run(BOT_TOKEN)
