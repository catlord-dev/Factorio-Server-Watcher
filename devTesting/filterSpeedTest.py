import os
import sys
import time
import random
import string
from timeit import timeit
import ahocorasick
import numpy as np
import orjson
import tqdm

sys.path.append(os.path.abspath("./devTesting"))
import filterSpeedTestCythonMod as cythonFilterThingy


# Helper function to generate random strings
def generate_random_string(length):
    return ("!" if random.randint(0, 1) else "") + "".join(
        random.choices(string.ascii_letters + string.digits, k=length)
    )


# Method 2: Using Aho-Corasick algorithm
def build_automaton(patterns, returnPrefix=""):
    A = ahocorasick.Automaton()
    for pattern in patterns:
        A.add_word(pattern, returnPrefix + pattern)
    A.make_automaton()
    return A


def filterNormal(data: list, filters: list):

    def filterWord(word: str, filter: str):
        negate = filter.startswith("!")
        if negate:
            filter = filter[1:]
        match = filter in word
        return match != negate

    # @profile
    def filterString(string: str, filters: set | tuple):
        # hitfilters from list to set, slight speed up (17.2 to 16.6 sec), might just be runtime diff
        hitFilters = set()
        for filter in filters:
            if isinstance(filter, tuple):
                hit = True
                for subfilter in filter:
                    if not filterWord(string, subfilter):
                        hit = False
                        break
                if hit:
                    hitFilters.add(filter)
                    continue
            else:
                match = filterWord(string, filter)
                if match:
                    hitFilters.add(filter)
        return hitFilters

    for thing in data:
        filterString(thing, filters)


def filterAho(data: list, filters: list, autoDict: dict):

    def checkAuto(string: str, auto: ahocorasick.Automaton):
        try:
            hits = set()
            for pos, value in auto.iter(string):
                hits.add(value)
            return hits
        except AttributeError:
            return set()

    # @profile
    def filterString(
        string: str,
        filters: list,
        autoDict: dict,
    ):
        #

        hitFilters = set()
        hitNorm = checkAuto(string, autoDict["norm"])

        hitNots = checkAuto(string, autoDict["nots"])
        hitNots.intersection_update(autoDict["nots"])
        hitNots = ["!" + x for x in hitNots]

        hitTupleNorm = checkAuto(string, autoDict["tupleNorm"])

        hitTupleNots = checkAuto(string, autoDict["tupleNots"])
        hitTupleNots.intersection_update(autoDict["tupleNots"])
        hitTupleNots = ["!" + x for x in hitTupleNots]

        hitTupleFilters = hitTupleNorm.union(hitTupleNots)
        for filter in filters:
            if isinstance(filter, tuple):
                if hitTupleFilters.issuperset(filter):
                    hitFilters.add(filter)

        hitFilters.update(hitNorm)
        hitFilters.update(hitNots)

        return hitFilters

    for thing in data:
        filterString(thing, filters, autoDict)


def filterAhoSetup(filters: list):
    ahoFilters = dict()
    # tuples not , tuples, norm, nots
    norm = set()
    nots = set()
    tupleNorm = set()
    tupleNots = set()
    for filter in filters:
        if isinstance(filter, tuple):
            for subfilter in filter:
                if subfilter.startswith("!"):
                    tupleNots.add(subfilter[1:])
                else:
                    tupleNorm.add(subfilter)
        else:
            if filter.startswith("!"):
                nots.add(filter[1:])
            else:
                norm.add(filter)

    ahoFilters["norm"] = build_automaton(norm)
    ahoFilters["nots"] = build_automaton(nots)
    ahoFilters["tupleNorm"] = build_automaton(tupleNorm)
    ahoFilters["tupleNots"] = build_automaton(tupleNots)
    return ahoFilters


def filterCombined(data: list, filters: list, autoDict: dict):

    def filterWord(word: str, filter: str):
        negate = filter.startswith("!")
        if negate:
            filter = filter[1:]
        match = filter in word
        return match != negate

    def checkAuto(string: str, auto: ahocorasick.Automaton):
        try:
            hits = set()
            for pos, value in auto.iter(string):
                hits.add(value)
            return hits
        except AttributeError:
            return set()

    # @profile
    def filterString(
        string: str,
        filters: list,
        autoDict: dict,
    ):
        #

        hitFilters = set()
        hitNorm = checkAuto(string, autoDict["norm"])

        hitNots = checkAuto(string, autoDict["nots"])
        hitNots.intersection_update(autoDict["nots"])
        hitNots = ["!" + x for x in hitNots]

        for filter in filters:
            if isinstance(filter, tuple):
                hit = True
                for subfilter in filter:
                    if not filterWord(string, subfilter):
                        hit = False
                        break
                if hit:
                    hitFilters.add(filter)
                    continue

        hitFilters.update(hitNorm)
        hitFilters.update(hitNots)

        return hitFilters

    for thing in data:
        filterString(thing, filters, autoDict)


def testFilterLogicSpeed(data, fullData, filterAmtThing=5):

    loopAmt = 25
    filterLength = [5, 20]
    filterAmt = [filterAmtThing, filterAmtThing]
    subFilterLength = [5, 20]  # how long the words in the sub filters can be
    subFilterAmt = [3, 10]  # how many words in the sub filters
    subFilterChance = 0.1
    start = time.time()
    filters = []
    for i in range(random.randint(filterAmt[0], filterAmt[1])):
        if random.random() < subFilterChance:
            subFilters = []
            for j in range(random.randint(subFilterAmt[0], subFilterAmt[1])):
                subFilters.append(
                    generate_random_string(
                        random.randint(subFilterLength[0], subFilterLength[1])
                    )
                )
            filters.append(tuple(subFilters))
        else:
            filters.append(
                generate_random_string(random.randint(filterLength[0], filterLength[1]))
            )
    filters = set(filters)
    filters = {"name": filters, "tags": filters, "description": filters}
    # print(filters)
    stop = time.time()
    filterSetupTime = stop - start
    start = time.time()
    ahoFilters = filterAhoSetup(filters)
    stop = time.time()
    ahoSetupTime = stop - start

    normalTime = 0
    ahoTime = 0
    combinedTime = 0
    cythonTime = 0
    cython2Time = 0
    for i in range(loopAmt):
        start = time.perf_counter()
        filterNormal(data, filters)
        stop = time.perf_counter()
        normalTime += stop - start

        start = time.perf_counter()
        filterAho(data, filters, ahoFilters)
        stop = time.perf_counter()
        ahoTime += stop - start

        start = time.perf_counter()
        filterCombined(data, filters, ahoFilters)
        stop = time.perf_counter()
        combinedTime += stop - start

        start = time.perf_counter()
        for server in rawData:
            # print(server)
            cythonFilterThingy.filterCython(server, filters)
        stop = time.perf_counter()
        cythonTime += stop - start

        start = time.perf_counter()
        
        for server in rawData:
            # print(server)
            # print("123")
            cythonFilterThingy.filterCython2(server, filters)
            # exit(0)
            # print("1233")
        stop = time.perf_counter()
        cython2Time += stop - start

    # print(f"Filter Make Time      : {filterSetupTime*1000:>10.3f} ms\n")
    # # print(f"Aho Make Time         : {ahoSetupTime*1000:>10.3f} ms\n")
    # # print(f"Normal Time (Per)     : {(normalTime*1000)/loopAmt:>10.3f} ms")
    # # print(f"Normal Time (Total)   : {normalTime:>10.3f} sec\n")
    # # print(f"Aho Time (Per)        : {(ahoTime*1000)/loopAmt:>10.3f} ms")
    # # print(f"Aho Time (Total)      : {ahoTime:>10.3f} sec\n")
    # # print(f"Combined Time (Per)   : {(combinedTime*1000)/loopAmt:>10.3f} ms")
    # # print(f"Combined Time (Total) : {combinedTime:>10.3f} sec\n")
    # print(f"Cython Time (Per)     : {(cythonTime*1000)/loopAmt:>10.5f} ms")
    # print(f"Cython Time (Total)   : {cythonTime:>10.5f} sec\n")
    # print(f"Cython2 Time (Per)    : {(cython2Time*1000)/loopAmt:>10.5f} ms")
    # print(f"Cython2 Time (Total)  : {cython2Time:>10.5f} sec\n")
    # print(f"Total Time            : {normalTime+ahoTime+filterSetupTime+ahoSetupTime+combinedTime+cython2Time:>10.3f} sec")
    # return normalTime,filterSetupTime

    return (
        (normalTime * 1000) / loopAmt,
        (ahoTime * 1000) / loopAmt,
        (combinedTime * 1000) / loopAmt,
        (cythonTime * 1000) / loopAmt,
        (cython2Time * 1000) / loopAmt,
    )

    """ 
    50 , .25 -  98   ms for normal , 32   ms for cython , 3.06x faster
    50 , .5  - 109.4 ms for normal , 31.5 ms for cython , 3.47x faster
    50 , .75 - 126   ms for normal , 37.5 ms for cython , 3.36x faster
    50 , 1   - 160   ms for normal , 50.5 ms for cython , 3.17x faster
    """


# # Generate test data
# def genData(string1Amt,string2Amt):
#     string1_list = [generate_random_string(random.randint(5, 50)) for _ in range(string1Amt)]
#     string2_list = [generate_random_string(random.randint(5, 20)) for _ in range(string2Amt)]

#     # Method 1: Using a for loop with `in` statement
#     def check_patterns_with_in(strings_list, patterns):
#         results = []
#         for string1 in strings_list:
#             hits = {s for s in patterns if s in string1}
#             results.append(hits)
#         return results


#     def check_patterns_with_automaton(strings_list, automaton):
#         results = []
#         for string1 in strings_list:
#             hits = set()
#             for end_index, original_value in automaton.iter(string1):
#                 hits.add(original_value)
#             results.append(hits)
#         return results

#     # Benchmark Method 1: `in` statement
#     start_time = time.time()
#     results_in = check_patterns_with_in(string1_list, string2_list)
#     time_in = time.time() - start_time

#     # Benchmark Method 2: Aho-Corasick
#     start_time = time.time()
#     automaton = build_automaton(string2_list)

#     results_aho = check_patterns_with_automaton(string1_list, automaton)
#     time_aho = time.time() - start_time
#     assert results_in == results_aho, "The results differ between the methods!"
#     return time_in, time_aho
import matplotlib.pyplot as plt


with open("FactorioServers.json", "rb") as f:
    rawData = orjson.loads(f.read())

data = set()
start = time.perf_counter()
for server in rawData:
    data.add(server["name"])
    data.add(server["description"])
    if "tags" in server:
        for tag in server["tags"]:
            data.add(tag)

data = set(random.choices(list(data), k=6))

stop = time.perf_counter()
startupTime = stop - start
print(f"Startup Time          : {startupTime*1000:>10.3f} ms")
# testFilterLogicSpeed(data,rawData,5)
# exit(0)


times1 = []
times2 = []
times3 = []
times4 = []
times5 = []
amts = []
scale = 1
amt = 300
bar = tqdm.tqdm(total=sum(range(1, 100)))
for i in range(1, 100):
    bar.update(i)
    tmpTime1 = []
    tmpTime2 = []
    tmpTime3 = []
    tmpTime4 = []
    tmpTime5 = []
    for ii in range(1):
        inTime, ahoTime, combinedTime, cythonTime, cython2Time = testFilterLogicSpeed(
            data, i
        )
        tmpTime1.append(inTime)
        tmpTime2.append(ahoTime)
        tmpTime3.append(combinedTime)
        tmpTime4.append(cythonTime)
        tmpTime5.append(cython2Time)
    times1.append(sum(tmpTime1) / len(tmpTime1) * scale)
    times2.append(sum(tmpTime2) / len(tmpTime2) * scale)
    times3.append(sum(tmpTime3) / len(tmpTime3) * scale)
    times4.append(sum(tmpTime4) / len(tmpTime4) * scale)
    times5.append(sum(tmpTime5) / len(tmpTime5) * scale)
    amts.append(i)

bar.close()

def moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size) / window_size, mode="valid")

plt.plot(amts[len(amts) - len(moving_average(times1, 5)) :],
        moving_average(times1, 5))
plt.plot(amts[len(amts) - len(moving_average(times2, 5)) :],
        moving_average(times2, 5))
plt.plot(amts[len(amts) - len(moving_average(times3, 5)) :],
        moving_average(times3, 5))
plt.plot(amts[len(amts) - len(moving_average(times4, 5)) :],
        moving_average(times4, 5))
plt.plot(amts[len(amts) - len(moving_average(times5, 5)) :],
        moving_average(times5, 5))


plt.legend(
    ["Normal", "Aho", "Combined", "Cython", "Cython2"],
)  # cython is cythonized version of the normal filter with cdef and all that stuff

plt.xlabel("Filter Amt")
plt.ylabel("ms")
plt.show()
exit()
"""



so AHO scales very well in scaling string2 amount
scales with very simular time compared to linar with just using the in statement

AHO should be used for the first big filter where there is 2-3k servers and when there starts be to be a lot of filters, like a lot alot of filters
the big thing being, is that there is a cost to remaking the automaton, the pattern that is used by AHO, even more so because we got to seperate out filters into normal, negates , and tuples



"""
start = time.time()
bar = tqdm.tqdm(total=1000)

times = []
amts = []
for i in range(1000):
    bar.update(1)
    patList = [generate_random_string(random.randint(5, 50)) for _ in range(i)]
    tim = timeit(lambda: build_automaton(patList), number=100)
    times.append(tim * 10)
    amts.append(i)
bar.close()

slope3, slope2, slope, intercept = np.polyfit(amts, times, 3)
lineofbestfit = (
    np.array(amts) * (slope3**3)
    + np.array(amts) * (slope2**2)
    + slope * np.array(amts)
    + intercept
)
plt.plot(amts, times)
plt.plot(amts, lineofbestfit, label="Best Fit")
print(f"{(tim):.2f} ms per")
print(f"Total time: {time.time() - start:.4f} seconds")
plt.show()
