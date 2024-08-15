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

    bot.watchedServers = {}
    bot.filters = {"changed": True}
    bot.filterLookup = {"changed": True, "tags": {}, "name": {}, "description": {}}

    serversConfig: dict = bot.serversConfig
    watchedServers: dict = bot.watchedServers
    filterLookup: dict = bot.filterLookup
    filters: dict = bot.filters

    print("Starting server watcher with watch interval: " + str(watchInterval))
    while True:
        print("Getting games")
        games = getGames(factorioUsername, factorioToken)
        await filterGames(bot, games)
        await asyncio.sleep(60)


def getFilters(serversConfig: dict, filterType: str = "all"):
    """
    makes a set of all the filters of the type set
    if filterType is 'all', a dict of sets is returned, each set is a different filter type
    otherwise, a single set is returned, being the filter type specified



    """

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
        return filters
    return None


def makeLookup(serversConfig: dict):
    """
    Create a dictionary that uses filters as keys to lookup what discord servers (the server id) has that filter.

    Args:
        serversConfig (dict): A dictionary containing the configuration of the servers.

    Returns:
        dict: A dictionary containing the lookup information.
             The dictionary has the following structure:
             {
                 "tags": {
                     filter1: [server1, server2, ...],
                     filter2: [server3, server4, ...],
                     ...
                 },
                 "name": {
                     filter1: [server5, server6, ...],
                     filter2: [server7, server8, ...],
                     ...
                 },
                 "description": {
                     filter1: [server9, server10, ...],
                     filter2: [server11, server12, ...],
                     ...
                 },
                 "changed": bool
             }
             The "changed" field indicates whether the lookup information has changed since the last time it was generated. This is used to tell whether this lookup table should be remade
             idealy, any changes to filters should also change this so it is correct since remaking it could be costly in performance if there is a lot of filters and/or discord servers
    """
    filterLookup = {"tags": {}, "name": {}, "description": {}, "changed": False}

    for s, config in serversConfig.items():
        if s == "comments":
            continue
        filters = config["filters"]
        for tag in ["tags", "name", "description"]:
            for fil in filters[tag]:
                if fil in filterLookup[tag]:
                    filterLookup[tag][fil].append(s)
                else:
                    filterLookup[tag][fil] = set([s])
    return filterLookup


async def filterGames(bot: Client, games: list):
    # print(time.time())
    global lastCheckedID, lowestID
    serversConfig: dict = bot.serversConfig
    watchedServers: dict = bot.watchedServers
    filterLookup: dict = bot.filterLookup
    filters: dict = bot.filters

    if filters["changed"]:
        filters = getFilters(serversConfig)
        bot.filters = filters

    if filterLookup["changed"]:
        filterLookup = makeLookup(serversConfig)
        bot.filterLookup = filterLookup

    # sort games by game_id
    games.sort(key=lambda x: x["game_id"], reverse=True)

    # game ids are ints, not str ints
    # get the lowest and highest game_id
    curMin = games[0]["game_id"]
    curMax = games[-1]["game_id"]

    # if lowest stored id is greater than the current lowest id, update the lowest id because in theory, it's an incrementing value and this should be impossible, this catches that
    if lowestID > curMin:
        lowestID = curMin
        lastCheckedID = 0

    # make a dict of the current servers with the game_id as the key
    gamesByID = {game["game_id"]: game for game in games}

    # get a list of all the game_ids that is sorted
    keys = list(gamesByID.keys())

    # if the lastCheckedID is not in the list, add it and resort the list
    # if the lastCheckedID server closed then it would not be in the list
    if lastCheckedID not in keys:
        keys.append(lastCheckedID)
        keys.sort()
    # print(filters)
    # check current servers against watched servers, close servers that are not in the list
    closedGames = []

    for gameID in watchedServers.copy():
        if gameID not in keys:
            closedGames.append(closeServer(bot, gameID, watchedServers))
        else:
            #update server data
            watchedServers[gameID].update(gamesByID[gameID])

    await asyncio.gather(*closedGames)
    print(f"Closed {len(closedGames)} servers")

    openedGames = []

    # check new servers based on the last highest id
    for gameID in keys[keys.index(lastCheckedID) :]:
        server = gamesByID.get(gameID, None)
        if server is None:
            continue
        if gameID in watchedServers:
            continue
        filtersHit = checkFilters(server, filters)
        if filtersHit["hit"]:
            watchedServers[gameID] = server
            openedGames.append(openServer(bot, server, filtersHit))

    await asyncio.gather(*openedGames)
    print(f"Opened {len(openedGames)} servers")

def formatTime(time: int):
    hours = time // 60
    minutes = time % 60
    return f"{hours}h {minutes}m"


def formatMessage(msg: str, server: dict):
    # print(type(msg),type(server))
    msg = msg.replace("{gameId}", str(server["game_id"]))
    msg = msg.replace("{name}", server["name"])
    msg = msg.replace("{description}", server["description"])
    msg = msg.replace("{tags}", ",".join(server.get("tags", [])))
    msg = msg.replace("{maxPlayers}", str(server["max_players"]))
    msg = msg.replace(
        "{gameVersion}", str(server["application_version"]["game_version"])
    )
    msg = msg.replace("{playtime}", str(formatTime(server["game_time_elapsed"])))
    msg = msg.replace("{hasPassword}", str(server["has_password"]))
    msg = msg.replace("{serverId}", str(server["server_id"]))
    msg = msg.replace("{hostAddress}", str(server["host_address"]))
    msg = msg.replace("{hasMods}", str(server["has_mods"]))
    msg = msg.replace("{modCount}", str(server["mod_count"]))
    msg = msg.replace("{playerCount}", str(len(server["players"])))
    return msg


async def closeServer(bot: Client, gameID: int, watchedServers: dict):
    print(
        formatMessage(
            "```\n*** Server Closed ***\nGame ID: {gameId}\nName: {name}\nDescription: {description}\nPassword: {hasPassword}\nPlaytime: {playtime}\nMods: {modCount}\nPlayers: {playerCount}\nTags: {tags}\n```",
            watchedServers[gameID],
        )
    )
    watchedServers.pop(gameID)


async def openServer(bot: Client, server: dict, filters: dict):
    # print(time.time())
    filterLookup = bot.filterLookup
    guilds = []
    # print(filterLookup)
    for filterType in ["tags", "name", "description"]:
        for filter in filters[filterType]:
            # print(filterLookup[filterType])
            guilds.extend(filterLookup[filterType][filter])
    alerts = []
    for guildId in guilds:
        alerts.append(sendAlert(bot,guildId,server,openAlert=True))
        
        # print(guild,type(guild))
    # print(servers)
    await asyncio.gather(*alerts)
    print(
        formatMessage(
            "```\n*** Server Opened ***\nGame ID: {gameId}\nName: {name}\nDescription: {description}\nPassword: {hasPassword}\nPlaytime: {playtime}\nMods: {modCount}\nPlayers: {playerCount}\nTags: {tags}\n```",
            server,
        )
    )

async def sendAlert(bot: Client, guildId: int,server: dict,openAlert=True):
    guildConfig = bot.serversConfig[guildId]
    title = ""
    msg = ""
    color = ""
    embed = guildConfig["embed"]
    if embed:
        if openAlert:
            title = guildConfig["embed"]["open"]["title"]
            msg = guildConfig["embed"]["open"]["description"]
            color = guildConfig["embed"]["open"]["color"]
        else:
            title = guildConfig["embed"]["close"]["title"]
            msg = guildConfig["embed"]["close"]["description"]
            color = guildConfig["embed"]["close"]["color"]
    else:
        if openAlert:
            msg = guildConfig["alert"]["open"]
        else:
            msg = guildConfig["alert"]["close"]
    msg = formatMessage(msg, server)
    title = formatMessage(title, server)
    color = Color.from_hex(color)
    alerts = []
    for channelId in guildConfig["channels"]:
        channel: GuildChannel  = bot.get_channel(int(channelId))
        if embed:
            alerts.append(channel.send(embed=Embed(title=title, description=msg, color=color)))
        else:
            alerts.append(channel.send(msg))
    await asyncio.gather(*alerts)
        
        


def filterString(string: str, filters: set | tuple):
    """filters strings based on the following rules
    for each filter in the filters
        if the filter is in the string, then it saves the filter

    if the filter starts with ! then it negates the filter and does the opposite, where if the filter isn't in the string, then it saves the filter

    Args:
        string (str): the string to put filters against
        filters (dict): the filters to test against the string, should be a set or tuple, other iterables may work but better to use set and tuple
    """
    # print(f"{string} - {filters}")
    hitFilters = set()
    # go through all filters
    for filter in filters:
        # if the filter is a sub filter , represented as a tupe rather than list so it is hashable
        if isinstance(filter, tuple):
            hits = filterString(string, filter)
            # unlike normal filters, sub filters use AND logic rather than OR, so all filters in the sub filter have be hit for the sub filter to be considered hit
            if len(hits) == len(filter):
                hitFilters.add(filter)
                continue
        negate = False
        # if the filter starts with ! then negate the filter
        if string[0:1] == "!":
            negate = True
            string = string[1:]
        if filter in string or filter == string:
            if negate == False:
                # print("TRUE")
                hitFilters.add(filter)
        elif negate == True:
            hitFilters.add(filter)
    return hitFilters


def checkFilters(server: dict, filters: dict):

    ["tags", "name", "description"]
    hitFilters = {"tags": set(), "name": set(), "description": set(), "hit": False}
    for filterType in ["tags", "name", "description"]:
        # some servers don't have tags
        if filterType not in server:
            continue
        if filterType == "tags":
            for tag in server["tags"]:
                hitfilts = filterString(tag, filters[filterType])
                hitFilters["tags"].update(hitfilts)
        else:
            hitFilters[filterType] = filterString(
                server[filterType], filters[filterType]
            )
        if len(hitFilters[filterType]) > 0:
            hitFilters["hit"] = True
    return hitFilters
