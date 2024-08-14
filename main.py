import asyncio
import json
import os
import shutil
import time
from interactions import Client, Intents, SlashContext, Snowflake, listen, slash_command
from interactions.api.events import Startup
import newWatcher as watcher
import configManager




botConfig , serversConfig = configManager.main()

debug= ""


# Create the bot
bot = Client(intents=Intents.new(messages=True,message_content=True,guild_messages=True,guilds=True,guild_members=True))

bot.config = botConfig
bot.serversConfig = serversConfig


@listen(Startup)
async def on_ready():
    print(f'Logged in as {bot.user.display_name} ({bot.user.id})')
    print('------')
    print(f"Owner ID: {bot.owner}")
    await watcher.main(bot)


bot.delete_unused_application_cmds = True
bot.load_extension("commands")
bot.load_extension("components")
bot.load_extension("events")
bot.start(bot.config["botToken"])
