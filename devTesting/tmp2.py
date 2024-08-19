from ast import Param
import hashlib
import time
import requests




def formatParms(msg:str,user:str,x:int,y:int,z:int,secret):
    return f"?text={msg.replace(' ', '+')}&username={user}&x={x}&y={y}&z={z}&secret={secret}"



def makeSecret():
    tim = time.time()
    print(tim)
    tim = int(tim//100*100)
    print(tim)
    sec = str(tim)+"QMk6AFdKRYIy6P6hzwsQ4du7OUQgmelRM/lkPJXBCqk="
    thing = hashlib.sha256()
    thing.update(sec.encode("utf-8"))
    return thing.hexdigest()


msg = "The IP is flat.spifftopia.net"
user = "Connerbrow"
x=420
y=6969
z=-420
url = "https://higuyswelcometomyvlog.loophole.site/requests"
print(url+formatParms(msg,user,x,y,z,makeSecret()))
# exit()
print("before")
req = requests.post(url+formatParms(msg,user,x,y,z,makeSecret()),headers={"Accept": "application/json"})
print(req.json())
print("after")
# print(makeSecret())