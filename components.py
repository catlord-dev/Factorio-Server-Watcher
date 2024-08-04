from interactions import ComponentContext, Extension, component_callback, ComponentType,Client
from FactorioAPI.API.Internal.matchmaking import getGameDetails


class componentCallbacks(Extension):
    # print("meow")
    @component_callback("mods")
    async def on_component(ctx: ComponentContext):
        print("Duid a thing.")    
        print(ctx.custom_id)
        
    @component_callback("players")
    async def on_component(ctx: ComponentContext):
        print("Duid a thing. 2")    
        print(ctx.custom_id)



print("loaded")