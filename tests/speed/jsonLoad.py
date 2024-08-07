import json
import time
import orjson
import timeit

#from chatgpt
def measure_performance(func, number=3, repeat=3):
    t = timeit.Timer(lambda: func())
    execution_times = t.repeat(repeat=repeat, number=number)
    avg_time = sum(execution_times) / len(execution_times) / number
    print(f"Average execution time over {repeat} runs: {avg_time:.8f} seconds")

print("Generating test data")
start = time.time()
#make a dummy server.json file with 10k servers
servers = 10_000

basePath = "./default/servers.json"
perServerPath = "./default/perServer.json"

dummyDataPath = "./tests/speed/dummyData.json"

with open(basePath,"r") as f:
    dummyData = json.load(f)
with open(perServerPath,"r") as f:
    perServerData = json.load(f)

for i in range(servers):
    dummyData[str(i)] = perServerData
    
with open(dummyDataPath,"w") as f:
    json.dump(dummyData,f,indent=4)
stop = time.time()
print(f"Generated dummy data in {stop - start:.5f} seconds")


def jsonTest():
    with open(dummyDataPath,"r") as f:
        data = json.load(f)
    with open(dummyDataPath,"w") as f:
        json.dump(data,f,indent=4)
        
def orjsonTest():
    with open(dummyDataPath,"rb") as f:
        data = orjson.loads(f.read())
    with open(dummyDataPath,"wb") as f:
        f.write(orjson.dumps(data, f, option=orjson.OPT_INDENT_2))
        
print("Testing Json")
start = time.time()
measure_performance(jsonTest)
start2 = time.time()
print(f"Total time: {start2 - start:.5f} seconds")
print("Testing Orjson")
measure_performance(orjsonTest)
start = time.time()
print(f"Total time: {start - start2:.5f} seconds")

# def using orjson, i wouldn't normally mess with it but the is seems to be over 10x faster , so while this many servers won't be used, it's still a good idea

#Stats
# Generating test data
# Generated dummy data in 1.37686 seconds
# Testing Json
# Average execution time over 3 runs: 1.53985488 seconds
# Total time: 13.85950 seconds
# Testing Orjson
# Average execution time over 3 runs: 0.09955706 seconds
# Total time: 0.89723 seconds