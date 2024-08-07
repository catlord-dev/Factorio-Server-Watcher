# main
starts up watcher and the config manager (prob config manager first)
logins in bot and starts event loop

# watcher
every X seconds (set by watch interval) the current server list will be gotten using FactorioAPI
servers will be gone through to find those that match the current filters
new servers will have alerts sent out
old/closed servers will be handled based on config

since alerts and filters are per server, it will be important to be fast
as such here are some idea for making code fast

server list can be checked for certain things to decide to not filter it
such as checking length or hash or something

filters can be hashed and cached

server ids can be hashed and cached

with the 2 things above, we can
prevent checking a server with a filter that we already did in the same for loop
prevent checking a server with a filter that was checked last time
it will be important to make sure the cache doesn't get too big, cache manager or something, make it as simple as possible/within reason

make logic as simple as it needs to be without making it hard to read


# config manager
manages the main config file along with the config for each server the bot is in
will manager file io of both kinds of config
will have methods to be used to read and write config
will read config file at start
will write config file when config changes

# commands
stuff for cmds, for most stuff, getters will also have to be made, so users don't have to check their config file all the time
making sure stuff such as bot or factorio token can only be set through the config file for security, also the bot wouldn't be able to make any cmds with the bot token
this will have to be setup per server, so setup config as needed
set alert message and related
set alert type , embed or text
set admin role
set tag filter
set name filter
set description filter
set mod filter
set watch interval (we are not doing per server config for this, because it would be pain to manage who knows how many watch loops of different intervals and filtering some servers but not others, and it's like, if your gonna get servers faster on one server, why not all of them, we already got the servers, just filter them)
find server with filters
set how alerts from closed servers are handled (delete old msg, edit old msg, send new close alert)

# msg buttons
buttons on alerts for open servers , one for modlist ,one for player list
will list mods 
will list players


# FactorioAPI
manages geting the server list and game details
overall managers interacting with factorio/wube servers

# other
overall , good documentation is very important, both in code and in how to use the bot, some may be made afterwards but documentation while coding will be important
features will be worked on first, then speed (speed won't be disregarded but it won't be top priority first)