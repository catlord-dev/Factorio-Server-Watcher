import asyncio
import json
import time
from FactorioAPI.API.Internal.matchmaking import getGames
from interactions import Client, Color, Embed, EmbedField, GuildChannel, Message


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
            await closeAlert(bot, alert, server)
        time.sleep(2)
        
def checkTag(filterTag:str,serverTags:list):
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

def checkFilter(bot: Client,filters:list,serverTags:list):
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
            if all(checkTag(tag,serverTags) for tag in filter):
                return True
        elif type(filter) == str:
            return checkTag(filter,serverTags)

async def filterServers(bot: Client, servers: list[dict]):
    print("filtering servers")
    start = time.time()
    config = bot.config
    tags = config["tags"]
    newServersCount = 0
    for gameId in bot.watchedServers.keys():
        bot.watchedServers[gameId]["watchKeepAlive"] = False
    for server in servers:
        if checkFilter(bot, tags, server["tags"]):
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
            await sendAlert(bot, server)
    print(f"Found {newServersCount} servers in {time.time() - start:.5f} seconds")
    closeGamesCnt = 0
    start = time.time()
    for server in bot.watchedServers.values():
        if not server["watchKeepAlive"]:
            print(f"Closing server alert: {server['game_id']}")
            closeGamesCnt += 1
            await closeAlert(bot, server["alert"], server)
    print(f"Closed {closeGamesCnt} servers in {time.time() - start:.5f} seconds")


async def sendAlert(bot: Client, server: dict):
    start = time.time()
    config = bot.config
    channelId = config["channelId"]
    if channelId == 0:
        print("No channel id set, not sending alert")
        return
    if(config["embed"]):
        alert = await bot.get_channel(channelId).send(embed=createEmbedAlert(server))
    else:
        alert = await bot.get_channel(channelId).send(createAlert(server))
    
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
Tags: ``{", ".join(server["tags"])}``""",color=Color.from_hex("#237feb")
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
Tags: ``{", ".join(server["tags"])}``""",color=Color.from_hex("#ED4245")
    )


def formatTime(time: int):
    return f"{time//3600}h {time // 60 % 60}m {time % 60}s"


async def closeAlert(bot: Client, alert: Message, server: dict):
    config = bot.config
    match config["closeAlert"]:
        case "delete":
            print("Deleting alert")
            print(alert.id)
            print(await alert.delete())
        case "edit":
            if config["embed"]:
                await alert.edit(embed=createCloseEmbedAlert(server))
            else:
                await alert.edit(content=createCloseAlert(server))
        case "closeAlert":
            if config["embed"]:
                await alert.edit(embed=createCloseEmbedAlert(server))
            else:
                await alert.channel.send(createCloseAlert(server))
        case _:
            pass
