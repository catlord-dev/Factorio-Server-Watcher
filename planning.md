# Discord Bot
will use the FactorioAPI library to get information about currently open factorio servers
this information will be filtered based on critera, from there alerts will be sent the selected channel that servers are open (send server details?)
based on config, when servers close, another alert could be sent saying it is down, the server open msg could be deleted (maybe also send close alert?), or the open message could be edited to a closed msg

## critera
this will be how the servers are filtered to figure out what alerts to send out
this will start with just checking the servers tags but in the future, more complicated filters could be added

## stuff
a list of sent alerts will have to be saved if we want to affect them later , it's better than searching through the channel for the message
a list of servers should also be saved so we can tell if the server is closed by checking the list for servers that aren't on the list sent by FactorioAPI

## cmds
### list open servers?
would have to be epherial (only cmd sender can see msg), to help prevent spam
### config cmd?
not sure, i think it's best to stick to a read only config file for now, read only because otherwise we would have to deal with changes after writing, either the config is saved when the program closes or at intervals, either way , the bot would have to be fully down for config to be changed, better it be read only so people can change config then just do a quick restart, minminal down time

### help cmd
prob a good idea, would just list itself and the list servers cmd

## the alerts
these should prob be embeds for style/looks, will look better and most likely better segment alerts that may be close together