from io import BytesIO
import FactorioAPI.Utils
import orjson
import os
import shutil
import FactorioAPI

"""
At start configs must be read from file and writeable file handle must be gotten 
configs must be validated

every method that sets configs must save the config to file

configs will be in a global var in this file so they can be accessed everywhere, thought setting configs should be done through the methods in this file

validatePath handles making sure config options exist, further data validation if possible is done after


"""

botConfigHandle: BytesIO = None
serversConfigHandle: BytesIO = None
perServerConfig: dict = None


def validatePath(
    config: dict, path: str, shouldBeType: type, prefix="", noRecurse=False
):
    """validates that the path exists and is of the correct type
    also validates paths before this path

    Args:
        config (dict): the config
        path (str): the . deliminated path
        shouldBeType (type): the type that the path should be
        prefix (str, optional): what prefix to add to the error message. Defaults to "".
    """
    if not noRecurse:
        leng = path.count(".")
        if leng > 1:
            validatePath(config, path[0 : path.rindex(".")], dict, prefix)

    tmpConfig = config.copy()
    for pat in path.split("."):
        tmpConfig = tmpConfig.get(pat, None)
        if tmpConfig is None:
            break
    if tmpConfig is None:
        raise Exception(
            prefix
            + "Path "
            + path
            + " does not exist, it should be of type "
            + shouldBeType.__name__
        )
    if not isinstance(tmpConfig, shouldBeType):
        raise Exception(
            prefix + "Path " + path + " is not of type " + shouldBeType.__name__
        )


def validateBotConfig(config):
    # not easy to do data checks, so just doing type and exist checks

    validatePath(config, "botToken", str, prefix="[Main Config] ")

    validatePath(config, "watchInterval", int, prefix="[Main Config] ")

    if config["watchInterval"] <= 0:
        raise Exception(
            "[Main Config] watchInterval can not be less than or equal to 0"
        )

    validatePath(config, "factorioToken", str, prefix="[Main Config] ")

    validatePath(config, "factorioUsername", str, prefix="[Main Config] ")


def validateServerConfig(config, name):
    """to be used by validateServersConfig recursively

    Args:
        config (dict): the config for a single server
    """
    # serverId:str, serverName:str, adminRole:str , alert.open:str, alert.close:str, embed.useEmbed:bool, embed.open.title:str, embed.open.description:str, embed.open.color:str, embed.close.title:str, embed.close.description:str, embed.close.color:str, buttons.players.enabled:boolean , buttons.players.color:int, buttons.modlist.enabled:boolean, buttons.modlist.color:int, closeAlert:str, filters.tags:list , filters.name:list, filters.description:list, channels:list

    prefix = f"[Server {name} Config] "

    validatePath(config, "serverId", str, prefix=prefix)

    validatePath(config, "serverName", str, prefix=prefix)

    validatePath(config, "adminRole", str, prefix=prefix)

    validatePath(config, "alert.open", str, prefix=prefix)

    validatePath(config, "alert.close", str, prefix=prefix)

    validatePath(config, "embed.useEmbed", bool, prefix=prefix)

    validatePath(config, "embed.open.title", str, prefix=prefix)

    validatePath(config, "embed.open.description", str, prefix=prefix)

    validatePath(config, "embed.open.color", str, prefix=prefix)

    validatePath(config, "embed.close.title", str, prefix=prefix)

    validatePath(config, "embed.close.description", str, prefix=prefix)

    validatePath(config, "embed.close.color", str, prefix=prefix)

    validatePath(config, "buttons.players.enabled", bool, prefix=prefix)

    validatePath(config, "buttons.players.color", int, prefix=prefix)

    validatePath(config, "buttons.modlist.enabled", bool, prefix=prefix)

    validatePath(config, "buttons.modlist.color", int, prefix=prefix)

    validatePath(config, "closeAlert", str, prefix=prefix)

    validatePath(config, "filters.tags", list, prefix=prefix)

    validatePath(config, "filters.name", list, prefix=prefix)

    validatePath(config, "filters.description", list, prefix=prefix)

    validatePath(config, "channels", list, prefix=prefix)

    # now for data validation
    # buttons color has to be between and including 1 and 4
    # closeAlert has to be nothing, edit , delete , closeAlert
    # ensure the lists in filters and channels are lists of strings, filters can have lists in them in the first list but those lists must be strings

    if (
        config["buttons"]["players"]["color"] < 1
        or config["buttons"]["players"]["color"] > 4
    ):
        raise Exception(f"{prefix}buttons.players.color must be between 1 and 4")

    if (
        config["buttons"]["modlist"]["color"] < 1
        or config["buttons"]["modlist"]["color"] > 4
    ):
        raise Exception(f"{prefix}buttons.modlist.color must be between 1 and 4")

    if config["closeAlert"] not in ["nothing", "edit", "delete", "closeAlert"]:
        raise Exception(
            f"{prefix}closeAlert must be nothing, edit , delete, or closeAlert"
        )

    for channel in config["channels"]:
        if not isinstance(channel, str):
            raise Exception(f"{prefix}channels must be a list of strings")

    for filterType in ["tags", "name", "description"]:
        validateFilter(config["filters"][filterType], prefix, filterType)


def validateFilter(filter: list, prefix, typ) -> None:
    for lay1 in filter:
        if isinstance(lay1, list):
            for lay2 in lay1:
                if not isinstance(lay2, str):
                    raise Exception(
                        f"{prefix}{typ} filter list must be a list of strings"
                    )
        elif not isinstance(lay1, str):
            raise Exception(
                f"{prefix}{typ} filters must be a list of strings or a string"
            )


def validateServersConfig(config: dict):
    for serverId in config.keys():
        if serverId == "comments":
            continue
        validateServerConfig(config[serverId], serverId)


def processServerConfig(config: dict, serverId: str):
    filters = ["tags", "name", "description"]
    
    for filter in filters:
        config[serverId]["filters"][filter] = set(
            [
                tuple([xx.lower() for xx in x]) if isinstance(x, list) else x.lower()
                for x in config[serverId]["filters"][filter]
            ]
        )


def processServersConfig(config: dict):
    for serverId in config.keys():
        if serverId == "comments":
            continue
        processServerConfig(config, serverId)
        
def updateValue(path:str,config:dict,perServerConfig:dict):
    """can only handle 1 path, no nesting

    Args:
        path (str): _description_
        config (dict): _description_
        perServerConfig (dict): _description_
    """
    config[path] = config.get(path, perServerConfig[path])

def updateServerConfig(config: dict, serverId: str,perServerConfig: dict):
    
    updateValue("showPassworded", config, perServerConfig)
    
    pass

def updateServersConfig(config: dict, perServerConfig: dict):
    for serverId in config.keys():
        if serverId == "comments":
            continue
        updateServerConfig(config[serverId], serverId, perServerConfig)

def main():
    global botConfigHandle, serversConfigHandle, perServerConfig
    FactorioAPI.Utils.APPLINK = "https://github.com/catlord-dev/Factorio-Server-Watcher"
    FactorioAPI.Utils.VERSION = "1.0.0"
    FactorioAPI.Utils.APPNAME = "FactorioServerWatcher"

    botConfig = {}
    serversConfig = {}
    tempConfig = {}
    botConfigPath = "./config.json"
    serversConfigPath = "./data/servers.json"
    perServerConfigPath = "./default/perServer.json"

    if not os.path.exists(botConfigPath):
        shutil.copyfile("./default/config.json", botConfigPath)

    os.makedirs("./data", exist_ok=True)
    if not os.path.exists(serversConfigPath):
        shutil.copyfile("./default/servers.json", serversConfigPath)

    with open(botConfigPath, "rb") as f:
        botConfig = orjson.loads(f.read())

    with open(serversConfigPath, "rb") as f:
        serversConfig = orjson.loads(f.read())
        
    botConfigHandle = open(botConfigPath, "ab")
    serversConfigHandle = open(serversConfigPath, "ab")
    perServerConfig = orjson.loads(open(perServerConfigPath, "rb").read())
    
    updateServersConfig(serversConfig,perServerConfig)
    flushFile(serversConfigHandle,serversConfig)
    
    validateBotConfig(botConfig)
    validateServersConfig(serversConfig)

    processServersConfig(serversConfig)

    
    
    

    return botConfig, serversConfig

def flushFile(file:BytesIO,jsonData:dict):
    file.seek(0)
    file.truncate(0)
    file.write(orjson.dumps(jsonData,option=orjson.OPT_INDENT_2))
    file.flush()

def addServer(serversConfig: dict, serverId: str, serverName: str):
    global serversConfigHandle, perServerConfig
    serversConfig[serverId] = perServerConfig.copy()
    serversConfig[serverId]["serverId"] = serverId
    serversConfig[serverId]["serverName"] = serverName
    flushFile(serversConfigHandle,serversConfig)


if __name__ == "__main__":
    main()
