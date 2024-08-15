import asyncio
import json
import sys
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
        start = time.time()
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
    def timeIt(msg,tim):
        print(f"{msg:<30}: {(time.time()-tim)*1000:.3f} ms")
        return time.time()
    tim = time.time()
    start = tim
    awaitedTime = 0
    global lastCheckedID, lowestID
    serversConfig: dict = bot.serversConfig
    watchedServers: dict = bot.watchedServers
    filterLookup: dict = bot.filterLookup
    filters: dict = bot.filters
    tim = timeIt("Init",tim)
    if filters["changed"]:
        filters = getFilters(serversConfig)
        bot.filters = filters
    tim = timeIt("Filter Set Got",tim)
    if filterLookup["changed"]:
        filterLookup = makeLookup(serversConfig)
        bot.filterLookup = filterLookup
        print("Filter Lookup Changed")
    tim = timeIt("FilterLookup Done",tim)
    # sort games by game_id
    games.sort(key=lambda x: x["game_id"], reverse=True)
    tim = timeIt("sort games by id",tim)
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
    tim = timeIt("Id lookup Done",tim)
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
    tim = timeIt("Before Close Check",tim)
    for gameID in watchedServers.copy():
        if gameID not in keys:
            closedGames.append(closeServer(bot, gameID, watchedServers))
        else:
            # update server data
            watchedServers[gameID].update(gamesByID[gameID])
    tim = timeIt("After Close Check",tim)
    await asyncio.gather(*closedGames)
    awaitedTime += time.time() - tim
    tim = time.time()
    print(f"Closed {len(closedGames)} servers")

    openedGames = []

    tim = timeIt("Before Open Check",tim)
    filterTime = 0 
    # check new servers based on the last highest id
    stringMem = 0
    stringCnt = 0
    filterMem = 0 
    filterCnt = 0
    for typ in ["tags", "name", "description"]:
        for filter in filters[typ]:
            filterMem+= sys.getsizeof(filter)
            filterCnt+=1
        
    for gameID in keys[keys.index(lastCheckedID) :]:
        server = gamesByID.get(gameID, None)
        if server is None:
            continue
        if gameID in watchedServers:
            continue
        filterStart = time.time()
        # for typ in ["tags", "name", "description"]:
        #     if typ == "tags":
        #         for tag in server.get("tags",[]):
        #             stringMem+= sys.getsizeof(tag)
        #             stringCnt+=1
        #     else:
        #         stringMem+= sys.getsizeof(server[typ])
        #         stringCnt+=1
        
        filtersHit = checkFilters(server, filters)
        filterTime+= time.time() - filterStart
        if filtersHit["hit"]:
            watchedServers[gameID] = server
            openedGames.append(openServer(bot, server, filtersHit))
    timeIt("Filter Check",time.time()-filterTime)
    tim = timeIt("After Open Check",tim)
    
    await asyncio.gather(*openedGames)
    awaitedTime += time.time() - tim
    tim = time.time()
    print(f"Opened {len(openedGames)} servers")
    # print(f"There are {stringCnt} strings from servers that take up {stringMem} bytes")
    # print(f"There are {filterCnt} filters that take up {filterMem} bytes")
    tim = timeIt("Total",start+awaitedTime)
    timeIt("Awaited Time",tim+awaitedTime)
    
    print("\n")


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
    print(watchedServers[gameID].get("Guilds", "nothing, oof"))
    filterLookup = bot.filterLookup
    guilds = watchedServers[gameID]["Guilds"]
    # print(filterLookup)
    stuffToAwait = []
    for guildId in guilds:
        serverConfig = bot.serversConfig[guildId]
        closeAlertType = serverConfig["closeAlert"]
        # nothing, edit, delete, closeAlert
        closeMsg = ""
        closeTitle = ""
        closeColor = ""
        embed = serverConfig["embed"]["useEmbed"]

        if embed:
            closeTitle = serverConfig["embed"]["close"]["title"]
            closeMsg = serverConfig["embed"]["close"]["description"]
            closeColor = serverConfig["embed"]["close"]["color"]
        else:
            closeMsg = serverConfig["alert"]["close"]
        closeMsg = formatMessage(closeMsg, watchedServers[gameID])
        closeTitle = formatMessage(closeTitle, watchedServers[gameID])
        closeEmbed = Embed(
            title=closeTitle, description=closeMsg, color=Color.from_hex(closeColor)
        )
        match closeAlertType:
            case "nothing":
                continue
            case "edit":

                for channelId in guilds[guildId]:
                    Alertmessage: Message = guilds[guildId][channelId]
                    if embed:
                        stuffToAwait.append(
                            Alertmessage.edit(
                                embed=Embed(
                                    title=closeTitle,
                                    description=closeMsg,
                                    color=Color.from_hex(closeColor),
                                )
                            )
                        )
                    else:
                        stuffToAwait.append(Alertmessage.edit(content=closeMsg))

            case "delete":
                for channelId in guilds[guildId]:
                    Alertmessage: Message = guilds[guildId][channelId]
                    stuffToAwait.append(Alertmessage.delete())
            case "closeAlert":
                for channelId in guilds[guildId]:
                    Alertmessage: Message = guilds[guildId][channelId]
                    channel = Alertmessage.channel
                    if embed:
                        stuffToAwait.append(channel.send(embed=closeEmbed))
                    else:
                        stuffToAwait.append(channel.send(content=closeMsg))
            case "closeAlertReply":
                for channelId in guilds[guildId]:
                    Alertmessage: Message = guilds[guildId][channelId]
                    channel = Alertmessage.channel
                    if embed:
                        stuffToAwait.append(Alertmessage.reply(embed=closeEmbed))

                    else:
                        stuffToAwait.append(Alertmessage.reply(content=closeMsg))
            case _:
                pass
    start = time.time()
    await asyncio.gather(*stuffToAwait)
    print(f"Await close stuff takes {time.time() - start:.5f} seconds" )
    # print(
    #     formatMessage(
    #         "```\n*** Server Closed ***\nGame ID: {gameId}\nName: {name}\nDescription: {description}\nPassword: {hasPassword}\nPlaytime: {playtime}\nMods: {modCount}\nPlayers: {playerCount}\nTags: {tags}\n```",
    #         watchedServers[gameID],
    #     )
    # )
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
        alerts.append(sendAlert(bot, guildId, server, openAlert=True))
    start = time.time()
    messageLookups: list = await asyncio.gather(*alerts)
    print(f"Await open stuff takes {time.time() - start:.5f} seconds" )
    guildLookup = dict()
    for i in range(len(messageLookups)):
        guildLookup[guilds[i]] = messageLookups[i]

    server["Guilds"] = guildLookup

    # print(
    #     formatMessage(
    #         "```\n*** Server Opened ***\nGame ID: {gameId}\nName: {name}\nDescription: {description}\nPassword: {hasPassword}\nPlaytime: {playtime}\nMods: {modCount}\nPlayers: {playerCount}\nTags: {tags}\n```",
    #         server,
    #     )
    # )


async def sendAlert(bot: Client, guildId: int, server: dict, openAlert=True):
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
        channel: GuildChannel = bot.get_channel(int(channelId))
        if embed:
            alerts.append(
                channel.send(embed=Embed(title=title, description=msg, color=color))
            )
        else:
            alerts.append(channel.send(msg))
    messages = await asyncio.gather(*alerts)
    messageLookup = dict()
    for i in range(len(messages)):
        messageLookup[guildConfig["channels"][i]] = messages[i]
    return messageLookup


def filterString(string: str, filters: set | tuple,earlyExit=False):
    """filters strings based on the following rules
    for each filter in the filters
        if the filter is in the string, then it saves the filter

    if the filter starts with ! then it negates the filter and does the opposite, where if the filter isn't in the string, then it saves the filter

    Args:
        string (str): the string to put filters against
        filters (dict): the filters to test 
        against the string, should be a set or tuple, other iterables may work but better to use set and tuple
    """
    # print(f"{string} - {filters}")
    hitFilters = set()
    # go through all filters
    for filter in filters:
        # if the filter is a sub filter , represented as a tupe rather than list so it is hashable
        if isinstance(filter, tuple):
            hits = filterString(string, filter,earlyExit=True)
            # unlike normal filters, sub filters use AND logic rather than OR, so all filters in the sub filter have be hit for the sub filter to be considered hit
            if len(hits) == len(filter):
                hitFilters.add(filter)
                continue
        noHit = True
        
        # if the filter starts with ! then negate the filter
        negate = filter.startswith("!")
        if negate:
            filter = filter[1:]
        if len(filter) <= len(string) and (filter in string or filter == string):
            if negate == False:
                # print("TRUE")
                hitFilters.add(filter)
                noHit = False
        elif negate == True:
            hitFilters.add(filter)
            noHit = False
        if earlyExit and noHit:
            return hitFilters
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
