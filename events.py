from interactions import Client, Extension, Guild, SlashContext, contexts, listen, slash_command
from interactions.api.events import GuildJoin
import configManager
# print("exma")

def addServer(bot:Client,guild: Guild):
    serversConfig: dict = bot.serversConfig
    guildId = guild.id
    if str(guildId) in serversConfig:
            return
    configManager.addServer(serversConfig,str(guildId),guild.name)
    print("Added Server/Guild : ",guild.name)

class Events(Extension):
    
    
    @listen("GuildJoin")
    async def onGuildJoin(self, ctx: GuildJoin):
        bot:Client = ctx.bot 
        if not bot.is_ready:
            print("Startup GuildJoin events, guild :",ctx.guild.name)
            addServer(bot,ctx.guild)
            return
        # print("Added Server/Guild : ",ctx.guild.name)
        addServer(bot,ctx.guild)