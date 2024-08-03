import asyncio
import json
import os
import shutil
import time
from interactions import Client, Intents, SlashContext, Snowflake, listen, slash_command
from interactions.api.events import Startup
import watcher

if not os.path.exists("config.json"):
    shutil.copyfile("default_config.json","config.json")


with open("config.json","r") as f:
    config = json.load(f)


# Create the bot
bot = Client(intents=Intents.DEFAULT,debug_scope=config["serverId"])

        

bot.config = config


@listen(Startup)
async def on_ready():
    print(f'Logged in as {bot.user.display_name} ({bot.user.id})')
    print('------')
    print(f"Owner ID: {bot.owner}")
    asyncio.create_task(watcher.main(bot))


bot.delete_unused_application_cmds = True
bot.load_extension("commands")
bot.start(config["botToken"])
