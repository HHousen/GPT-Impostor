import os
import logging
import sqlalchemy as db
from discord import Client, Intents
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
from helpers import run_gpt_inference, get_gpt_first_message
from models import Guild, User

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


BOT_TOKEN = os.environ["BOT_TOKEN"]
MESSAGE_CONTEXT_LIMIT = 50  # Max number of messages to send as context to AI model
GPT_INVALID_RESPONSE_MESSAGE = (
    "Sorry, I could not think of a good message. Please make "
    + "sure there are enough messages in this channel so that I can learn how you write."
)
guild_ids = [892604457030914098]
ping_mode_users = {}

bot = Client(intents=Intents.default())
engine = db.create_engine(os.environ["DATABASE_URL"])
slash = SlashCommand(bot, sync_commands=True)


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

    if message.guild.id in ping_mode_users.keys():
        user_id_to_impersonate = ping_mode_users[message.guild.id]
        message_mentions_ids = {x.id: x for x in message.mentions}
        if user_id_to_impersonate in message_mentions_ids.keys():
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


async def get_channel_webhook(channel):
    logger.debug("Getting channel %s's webhook...", channel.id)
    webhooks = await channel.webhooks()
    webhook = next((x for x in webhooks if x.name == str(channel.id)), False)
    if not webhook:
        webhook = await channel.create_webhook(name=channel.id)
    return webhook


async def get_previous_messages(channel, as_string=True):
    logger.debug("Getting channel %s's previous messages...", channel.id)
    previous_messages = await channel.history(limit=MESSAGE_CONTEXT_LIMIT).flatten()
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
    guild_ids=guild_ids,
)
async def monologue(ctx: SlashContext, max_messages=25):
    await ctx.defer(hidden=True)

    channel = bot.get_channel(ctx.channel_id)
    webhook = await get_channel_webhook(channel)

    previous_messages_str = await get_previous_messages(channel)

    gpt_response = run_gpt_inference(previous_messages_str, token_max_length=512)
    print(gpt_response)
    gpt_messages = [
        message.split(":", 1) for message in gpt_response.strip().split("\n")
    ]

    gpt_messages = gpt_messages[:max_messages]

    for content in gpt_messages:
        if len(content) <= 1:
            await ctx.send(
                GPT_INVALID_RESPONSE_MESSAGE,
                hidden=True,
            )
            return

    for user, message in gpt_messages:
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
    guild_ids=guild_ids,
)
async def sus(ctx: SlashContext, user=None):
    await ctx.defer(hidden=True)

    channel = bot.get_channel(ctx.channel_id)
    webhook, first_response_message = await gpt_channel_response(channel, user)

    if not first_response_message:
        await ctx.send(
            GPT_INVALID_RESPONSE_MESSAGE,
            hidden=True,
        )
    else:
        await webhook.send(
            first_response_message, username=user.name, avatar_url=user.avatar_url
        )
        await ctx.send("Fake message sent!", hidden=True)


async def gpt_channel_response(channel, user):
    webhook = await get_channel_webhook(channel)

    previous_messages_str = await get_previous_messages(channel)

    context = previous_messages_str + f"\n{user.name}: "
    print(f"> Context:\n{context}")

    gpt_response = run_gpt_inference(context, token_max_length=50)
    print(f"> GPT Response:\n{gpt_response}")

    first_response_message = get_gpt_first_message(gpt_response, user.name)
    return webhook, first_response_message


@slash.slash(
    name="setuser",
    description="Impersonate a specific user when they are pinged.",
    options=[
        create_option(
            name="user",
            description="Choose the user to impersonate.",
            option_type=6,
            required=True,
        )
    ],
    guild_ids=guild_ids,
)
async def setuser(ctx: SlashContext, user=None):
    ping_mode_users[ctx.guild_id] = user.id
    await ctx.send(f"Impersonating {user.name}.", hidden=True)


bot.run(BOT_TOKEN)
