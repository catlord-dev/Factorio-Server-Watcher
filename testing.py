import time
from timeit import repeat, timeit

start = time.time()
import pandas as pd
import orjson
import random
from numba import njit
import numpy as np

# import profile
letters = [
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
]

with open("./examples/serverConfigExample.json", "rb") as f:
    data: dict = orjson.loads(f.read())


def randomString(length):
    string = ""
    for i in range(length):
        string += random.choice(letters)
    return string


for i in range(100):
    data[str(i)] = data["123456789012345678"]
    for tag in ["tags", "name", "description"]:
        data[str(i)]["filters"][tag] = [randomString(30) for i in range(30)]
        for ii in range(10):
            data[str(i)]["filters"][tag].append([randomString(30) for i in range(30)])
            
for i in range(100, 200):
    data[str(i)] = data[str(i-100)]
    
    
print(f"startup {time.time() - start:.5f}")
start = time.time()
for s in data:
    if s == "comments":
        continue
    for tag in ["tags", "name", "description"]:
        data[s]["filters"][tag] = [
            tuple(x) if isinstance(x, list) else x for x in data[s]["filters"]["tags"]
        ]
        data[s]["filters"][tag] = set(data[s]["filters"][tag])

# with open("tmp.json","wb") as f:
#     f.write(orjson.dumps(data))
print(f"data change {time.time() - start:.5f}")

# filterLookup = {"tags": {}, "name": {}, "description": {}, "changed": False}
@profile
def getFilters(serversConfig: dict, filterType: str):
    filters = {
        "tags": set(),
        "name": set(),
        "description": set(),
    }
    filterLookup = {"tags": {}, "name": {}, "description": {}, "changed": False}
    for s,config in serversConfig.items():
        if s == "comments":
            continue
        filters2 = config["filters"]
        for tag in ["tags", "name", "description"]:
            filters[tag].update(filters2[tag])
            for fil in filters2[tag]:
                if fil in filterLookup[tag]:
                    filterLookup[tag][fil].append(s)
                else:
                    filterLookup[tag][fil] = [s]
    return filters

def getFilters2(serversConfig: dict, filterType: str):
    filters = {
        "tags": set(),
        "name": set(),
        "description": set(),
    }
    filterLookup = {"tags": {}, "name": {}, "description": {}}
    for tag in ["tags", "name", "description"]:
        filters[tag] = set()
        for s in serversConfig:
            if s == "comments":
                continue
            filter: list = serversConfig[s]["filters"][tag]
            filters[tag].update(filter)
            for fil in filter:
                filt:set  = filterLookup[tag].get(fil,set())
                # print(s)
                filt.add(s)
                if len(filt) == 1:
                    filterLookup[tag][fil] = filt
    return filters


# print(getFilters(data,"tags"))
tagFilters = getFilters(data, "tags")
timit = timeit(lambda: getFilters2(data, "tags"), number=1000)/1000
print(f"getFilters: {timit:.7f} s")
print(f"{1/timit:.2f} runs/s")
times = repeat(lambda: getFilters2(data, "tags"), repeat=1000, number=1)
    
# Sort the times to easily discard the outliers
times.sort()

# Discard the lowest and highest 'num_discard' results to remove outliers
trimmed_times = times[5:-5]

# Calculate and return the average time of the remaining runs
average_time = np.mean(trimmed_times)
print(f"getFilters: {average_time:.7f} s")
print(f"{1/average_time:.2f} runs/s")