from interactions import Extension, SlashContext, contexts, slash_command
# print("exma")

class SlashCommands(Extension):
    # Define a simple slash command
    @slash_command(name="test23", description="Says meow!2")
    async def hello(self, ctx: SlashContext):
        print("mew")
        await ctx.send(f"Hello, {ctx.author.mention} meow!2")
