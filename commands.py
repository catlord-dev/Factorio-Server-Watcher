from interactions import Extension, Permissions, SlashContext, contexts, slash_command

# print("exma")


class SlashCommands(Extension):
    """
    things to add cmds for
    admin role
    alerts msg for both open and close and embed and  color and all that
    the alert buttons and their color
    how to handle close alerts
    filters for tags, names, descriptions
    channels to send alerts too
    whether to show passworded servers

    """

    @slash_command(
        name="help",
        description="Sends you some info on the bot and it's cmds",
        default_member_permissions=Permissions.ADMINISTRATOR,
    )
    async def help(self, ctx: SlashContext):
        # print("mew")
        await ctx.send(
            f"""/botinfo - explains what this bot is and how it works
/adminRole add - 
/adminRole list - 
/adminRole remove - 
/alertsMsg Open - 
/alertsMsg Close - 
/embedAlertsMsg Open -
/embedAlertsMsg Close - 
/closeAlerts -
/filters tags - 
/filters names - 
/filters descriptions - 
/filters all -
/alertChannels - 
/showPasswordProtected -
                       """
        )





    # Define a simple slash command
    @slash_command(
        name="show_password_protected",
        description="toggles whether servers with a password will have an alert sent for them",
        default_member_permissions=Permissions.ADMINISTRATOR,scopes=[612680043789025291]
    )
    async def show_password_protected(self, ctx: SlashContext):
        # print("mew")
        servers: dict = self.bot.serversConfig
        server:dict = servers[str(ctx.guild_id)]
        toggle = server["showPassworded"]
        if toggle:
            server["showPassworded"] = False
            await ctx.send(f"Servers with passwords will no longer have alerts sent for them")
        else:
            server["showPassworded"] = True
            await ctx.send(f"Servers with passwords will have alerts sent for them")


    # Define a simple slash command
    @slash_command(
        name="test23",
        description="Says meow!2",
        default_member_permissions=Permissions.ADMINISTRATOR,
    )
    async def hello(self, ctx: SlashContext):
        print("mew")
        await ctx.send(f"Hello, {ctx.author.mention} meow!2")
