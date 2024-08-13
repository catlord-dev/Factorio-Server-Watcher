import asyncio
import json
import time
from FactorioAPI.API.Internal.matchmaking import getGames
from interactions import (
    ActionRow,
    Button,
    ButtonStyle,
    Client,
    Color,
    ComponentContext,
    Embed,
    EmbedField,
    Extension,
    GuildChannel,
    Message,
    component_callback,
    listen,
)
from interactions.api.events import Component, Startup

filterLookup = {"changed": True, "tags": {}, "name": {}, "description": {}}

watchedServers = {}

serversConfig = {}

filters = {"changed":True}

lastCheckedID = 0
lowestID = 2**64



async def main(bot: Client):
    """the main event loop of watching factorio servers

    Args:
        bot (Client): the discord bot object, used to pass varibles around and interact with discord
    """
    factorioUsername = bot.config["factorioUsername"]
    factorioToken = bot.config["factorioToken"]
    watchInterval = bot.config["watchInterval"]
    serversConfig = bot.serversConfig
    print("Starting server watcher with watch interval: " + str(watchInterval))
    while True:
        print("Getting games")
        games = getGames(factorioUsername, factorioToken)
        await filterGames(games)
        await asyncio.sleep(60)


def getFilters(serversConfig: dict, filterType: str = "all"):
    filters = {
        "tags": set(),
        "name": set(),
        "description": set(),
        "changed": False,
    }
    if filterType == "all":
        for tag in ["tags", "name", "description"]:
            filters[tag] = set()
            for s in serversConfig:
                if s == "comments":
                    continue
                filter: list = serversConfig[s]["filters"][tag]
                filters[tag].update(filter)
        return filters
    else:
        tag = filterType
        filters[tag] = set()
        for s in serversConfig:
            if s == "comments":
                continue
            filter: list = serversConfig[s]["filters"][tag]
            filters[tag].update(filter)
    return filters[tag]


def makeLookup(serversConfig: dict):
    filterLookup = {"tags": {}, "name": {}, "description": {},"changed": False}
    
    for s,config in serversConfig.items():
        if s == "comments":
            continue
        filters = config["filters"]
        for tag in ["tags", "name", "description"]:
            for fil in filters[tag]:
                if fil in filterLookup[tag]:
                    filterLookup[tag][fil].append(s)
                else:
                    filterLookup[tag][fil] = [s]
    return filterLookup

async def filterGames(games:list):
    global lastCheckedID, lowestID, serversConfig, filters, filterLookup,watchedServers
    if filters["changed"]:
        filters = getFilters(serversConfig)
        
    if filterLookup["changed"]:
        filterLookup = makeLookup(serversConfig)
    
    # sort games by game_id
    games.sort(key=lambda x: x["game_id"], reverse=True)
    
    
    # get the lowest and highest game_id
    curMin = games[0]["game_id"]
    curMax = games[-1]["game_id"]
    
    # if lowest stored id is greater than the current lowest id, update the lowest id because in theory, it's an incrementing value and this should be impossible, this catches that
    if lowestID > curMin:
        lowestID = curMin
        lastCheckedID = 0
    
    # make a dict of the current servers with the game_id as the key
    gamesByID = {game["game_id"]:game for game in games}
    
    #get a list of all the game_ids that is sorted
    keys = list(gamesByID.keys())
    
    # if the lastCheckedID is not in the list, add it and resort the list
    if lastCheckedID not in keys:
        keys.append(lastCheckedID)
        keys.sort()
        
    # check current servers against watched servers, close servers that are not in the list
    for gameID in watchedServers.copy():
        if gameID not in keys:
            closeServer(gameID)
            watchedServers.pop(gameID)

    
    # check new servers based on the last highest id
    for gameID in keys[keys.index(lastCheckedID):]:
        server = gamesByID.get(gameID, None)
        if server is None:
            continue
        if gameID in watchedServers:
            continue
        filtersHit = checkFilters(server, filters)
        if len(filtersHit) > 0:
            watchedServers[gameID] = server
            openServer(server,filtersHit)

def formatTime(time: int):
    hours = time // 60
    minutes = time % 60
    return f"{hours}h {minutes}m"
    


def formatMessage(msg:str, server:dict):
    msg = msg.replace("{gameId}", str(server["game_id"]))
    msg = msg.replace("{name}", server["name"])
    msg = msg.replace("{description}", server["description"])
    msg = msg.replace("{tags}", ",".join(server.get("tags", [])))
    msg = msg.replace("{maxPlayers}", str(server["max_players"]))
    msg = msg.replace("{gameVersion}", str(server["application_version"]["game_version"]))
    msg = msg.replace("{playtime}", str(formatTime(server["game_time_elapsed"])))
    msg = msg.replace("{hasPassword}", str(server["has_password"]))
    msg = msg.replace("{serverId}", str(server["server_id"]))
    msg = msg.replace("{hostAddress}", str(server["host_address"]))
    msg = msg.replace("{hasMods}", str(server["has_mods"]))
    msg = msg.replace("{modCount}", str(server["mod_count"]))
    msg = msg.replace("{playerCount}", str(len(server["players"])))
    return msg

def closeServer(gameID: int):
    print(formatMessage("```\n*** Server Closed ***\nGame ID: {gameId}\nName: {name}\nDescription: {description}\nPassword: {hasPassword}\nPlaytime: {playtime}\nMods: {modCount}\nPlayers: {playerCount}\nTags: {tags}\n```", watchedServers[gameID]))

def openServer(server: int, filters: dict):
    print(formatMessage("```\n*** Server Opened ***\nGame ID: {gameId}\nName: {name}\nDescription: {description}\nPassword: {hasPassword}\nPlaytime: {playtime}\nMods: {modCount}\nPlayers: {playerCount}\nTags: {tags}\n```", server))

def checkFilters(server: dict, filters: dict):
    if "O2theC" in server.get("players",[]):
        return ["O2theC"]
    else:
        return []