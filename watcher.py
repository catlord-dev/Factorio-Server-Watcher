import asyncio
import json
import time
from FactorioAPI.API.Internal.matchmaking import getGames
from interactions import ActionRow, Button, ButtonStyle, Client, Color, ComponentContext, Embed, EmbedField, Extension, GuildChannel, Message, component_callback, listen
from interactions.api.events import Component,Startup




async def main(bot: Client):
    print("Starting server watcher")

    config = bot.config

    username = config["factorioUsername"]
    factorioToken = config["factorioToken"]
    delay = config["watchInterval"]
    tags = config["tags"]
    closeAlertType = config["closeAlert"]

    bot.watchedServers = {}

    match closeAlertType:
        case "delete":
            closeAlertType = "delete"
        case "edit":
            closeAlertType = "edit"
        case "nothing":
            closeAlertType = "nothing"
        case "closeAlert":
            closeAlertType = "closeAlert"
        case _:
            closeAlertType = "delete"
            print(
                f'Invalid close alert type, defaulting to delete, Type given: "{closeAlertType}"'
            )
    config["closeAlert"] = closeAlertType
    print("Watching for servers that have one of these tags: " + str(tags))
    print("Or has one of these words in it's name " + str(config["serverNameCheckList"]))
    print("Close alert type: " + str(closeAlertType))
    try:
        while True:
            print("Getting server list")
            games = getGames(username=username, token=factorioToken)
            with open("servers.json", "w") as f:
                json.dump(games, f, indent=4)
            await filterServers(bot, games)
            del games
            time.sleep(delay)
    except KeyboardInterrupt:
        print("Stopping server watcher")
        for server in bot.watchedServers.values():
            print("Closing server alert:", server["game_id"])
            alert = server["alert"]
            await closeAlert(bot, alert, server,botShutdown=True)
    time.sleep(1)
    await bot.stop()
    


def checkTag(filterTag: str, serverTags: list):
    """
    Returns True if the tag is in the serverTags, False if it is not.
    If the filterTag starts with !, it will negate and return the opposite of the result.

    Args:
        filterTag (str): The filter tag to evaluate.
        serverTags (list): The list of tags associated with the server.

    Returns:
        bool: True if the server should be included, False if it should be excluded.
    """
    negate = False
    if filterTag[0] == "!":
        filterTag = filterTag[1:]
        negate = True
    if filterTag in serverTags:
        if negate:
            return False
        else:
            return True
    else:
        if negate:
            return True
        else:
            return False


def checkFilter(bot: Client, filters: list, serverTags: list):
    """
    Checks if any of the filters are met by the serverTags.
    Does OR logic between elements, any lists will have their elements use AND logic
    add ! before a tag to negate it and add NOT logic to it

    Args:
        bot (Client): The bot instance.
        filters (list): List of filters to check.
        serverTags (list): The tags of the server to check.

    Returns:
        bool: True if any of the filters are met, False otherwise.
    """
    for filter in filters:
        if type(filter) == list:
            if all(checkTag(tag, serverTags) for tag in filter):
                return True
        elif type(filter) == str:
            return checkTag(filter, serverTags)

def lowerIt(stuff: str| list):
    if type(stuff) == list:
        for i in range(len(stuff)):
            stuff[i] = stuff[i].lower()
    else:
        stuff = stuff.lower()
    return stuff

async def filterServers(bot: Client, servers: list[dict]):
    print("filtering servers")
    
    start = time.time()
    config = bot.config
    tags = config["tags"]
    serverNames = config["serverNameCheckList"]
    newServersCount = 0
    
    for gameId in bot.watchedServers.keys():
        bot.watchedServers[gameId]["watchKeepAlive"] = False
        
    sentAlerts = []
    for server in servers:
        if checkFilter(bot, tags, server.get("tags", [])) or checkFilter(bot, serverNames, server.get("name", "")):
            if server["game_id"] in bot.watchedServers:
                bot.watchedServers[server["game_id"]]["watchKeepAlive"] = True
                continue
            gameId = server["game_id"]
            server["watchKeepAlive"] = True
            bot.watchedServers[gameId] = server.copy()
            del server
            server = bot.watchedServers[gameId]
            print(f"Found server with tag: {server['name']} - {server['tags']}")
            newServersCount += 1

            sentAlerts.append(sendAlert(bot, server))

    print(f"Found {newServersCount} servers in {time.time() - start:.5f} seconds")
    
    closeGamesCnt = 0
    start = time.time()
    for server in bot.watchedServers.values():
        if not server["watchKeepAlive"]:
            print(f"Closing server alert: {server['game_id']}")
            closeGamesCnt += 1
            sentAlerts.append(closeAlert(bot, server["alert"], server))
    print(f"Closed {closeGamesCnt} servers in {time.time() - start:.5f} seconds")
    
    for sentAlert in sentAlerts:
        await sentAlert


async def sendAlert(bot: Client, server: dict):
    start = time.time()
    config = bot.config
    channelId = config["channelId"]
    if channelId == 0:
        print("No channel id set, not sending alert")
        return
    buttons = [Button(style=ButtonStyle.BLUE,label="Mods",custom_id="mods"), Button(style=ButtonStyle.BLUE,label="Players",custom_id="players")]
    if config["embed"]:
        alert = await bot.get_channel(channelId).send(embed=createEmbedAlert(server),components=buttons)
    else:
        alert = await bot.get_channel(channelId).send(createAlert(server),components=buttons)

    server["alert"] = alert
    print(f"Sent alert in {time.time() - start:.5f} seconds")


def createAlert(server: dict):
    return f"""```
*** Server Opened ***
Game ID: {server["game_id"]}
Name: {server["name"]}
Description: {server["description"]}
Password: {server["has_password"]}
Playtime: {formatTime(server["game_time_elapsed"])}
Mods: {server["mod_count"]}
Players: {len(server.get("players", []))}
Tags: {", ".join(server["tags"])}```"""


def createEmbedAlert(server: dict):
    return Embed(
        title="Server Opened",
        description=f"""
Game ID: ``{server["game_id"]}``
Name: {server["name"]}
Description: {server["description"]}
Password: {server["has_password"]}
Playtime: {formatTime(server["game_time_elapsed"])}
Mods: {server["mod_count"]}
Players: {len(server.get("players", []))}
Tags: ``{", ".join(server["tags"])}``""",
        color=Color.from_hex("#237feb"),
    )


def createCloseAlert(server: dict):
    return f"""```
*** Server Closed ***
Game ID: {server["game_id"]}
Name: {server["name"]}
Description: {server["description"]}
Password: {server["has_password"]}
Playtime: {formatTime(server["game_time_elapsed"])}
Mods: {server["mod_count"]}
Players: {len(server.get("players", []))}
Tags: {", ".join(server["tags"])}```"""


def createCloseEmbedAlert(server: dict):
    return Embed(
        title="Server Closed",
        description=f"""
Game ID: ``{server["game_id"]}``
Name: {server["name"]}
Description: {server["description"]}
Password: {server["has_password"]}
Playtime: {formatTime(server["game_time_elapsed"])}
Mods: {server["mod_count"]}
Players: {len(server.get("players", []))}
Tags: ``{", ".join(server["tags"])}``""",
        color=Color.from_hex("#ED4245"),
    )


def formatTime(time: int):
    return f"{time//3600}h {time // 60 % 60}m {time % 60}s"


async def closeAlert(bot: Client, alert: Message, server: dict,botShutdown = False):
    start = time.time()
    config = bot.config
    print(f"Closing alert: {server['game_id']}")
    alertType = config["closeAlert"]
    if botShutdown:
        alertType = config["botCloseAlert"]
    match alertType:
        case "delete":
            await alert.delete()
        case "edit":
            if config["embed"]:
                await alert.edit(embed=createCloseEmbedAlert(server),components=[])
            else:
                await alert.edit(content=createCloseAlert(server),components=[])
        case "closeAlert":
            if config["embed"]:
                await alert.channel.send(embed=createCloseEmbedAlert(server))
            else:
                await alert.channel.send(createCloseAlert(server))
        case _:
            print("Invalid close alert type")

    print(f"Closed alert in {time.time() - start:.5f} seconds")


@component_callback("mods")
async def on_component(ctx: ComponentContext):
    print("Duid a thing.")    
    print(ctx.custom_id)
    # ctx.send(ephemeral=True,content="Mod List")