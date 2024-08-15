import random
import string
import sys
import time
from memory_profiler import memory_usage
from tqdm import tqdm


def random_string(length):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))

cache = {}
def generate_cache():
    global cache
    bar = tqdm(total=1000)
    for _ in range(1000):  # 100 first-level keys
        bar.update(1)
        first_key = random_string(random.randint(3, 30))
        cache[first_key] = {}
        for _ in range(1000):  # 100 second-level keys per first-level key
            if random.choice([True, False]):
                second_key = random_string(random.randint(3, 30))
            else:
                second_key = tuple(
                    random_string(random.randint(3, 30))
                    for _ in range(random.randint(1, 10))
                )
            cache[str(first_key)+"-"+str(second_key)] = random.choice([True, False])
    return cache


def measure_memory():
    time.sleep(5)
    mem_usage_before = memory_usage((lambda: None), interval=0.1, max_usage=True)
    cache = generate_cache()
    time.sleep(5)
    mem_usage = memory_usage((lambda: None), interval=0.1, max_usage=True)
    return mem_usage_before, mem_usage


if __name__ == "__main__":
    mem_usage_before, memory_used = measure_memory()
    print(f"Memory usage before cache: {mem_usage_before:.4f} MiB")
    print(f"Memory usage after cache: {memory_used:.4f} MiB")
    print(f"Memory usage for cache: {memory_used-mem_usage_before:.4f} MiB")
    chrCount = 0
    boolCount = 0
    memCount= 0 
    for key1 in cache:
        chrCount+=len(key1)
        memCount+= sys.getsizeof(key1)
        # for key2 in cache[key1]:
        #     chrCount+=len(key2)
        #     memCount+= sys.getsizeof(key2)
        boolCount+= 1
        memCount+= sys.getsizeof(cache[key1])
            
    print(f"Total number of characters in cache: {chrCount:,}")
    print(f"Total number of booleans in cache: {boolCount:,}")
    print(f"Total number of bytes in cache: {memCount:,}")
