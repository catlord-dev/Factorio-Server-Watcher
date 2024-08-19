import time
import timeit
import random
import string
from operator import itemgetter
from matplotlib import pyplot as plt
import tqdm


# Generate a list of dictionaries with random data
def generate_data(num_elements):
    data = []
    for i in range(num_elements):
        # Generate random string values for 10 keys
        record = {
            f"key_{j}": "".join(random.choices(string.ascii_letters, k=10))
            for j in range(10)
        }
        # Add a unique integer key
        record["game_id"] = random.randint(0, 50_000_000)
        data.append(record)
    return data


# Function to sort using lambda
def sort_with_lambda(data):
    data.sort(key=lambda x: x["game_id"], reverse=True)


# Function to sort using itemgetter
def sort_with_itemgetter(data):
    data.sort(key=itemgetter("game_id"), reverse=True)


def sort_by_isolating(data):
    # Step 1: Extract game_id and original indices
    ids_with_index = [(record["game_id"], idx) for idx, record in enumerate(data)]

    # Step 2: Sort the extracted game_id list
    ids_with_index.sort(reverse=True)

    # Step 3: Reorder original list based on sorted indices
    sorted_data = [data[idx] for _, idx in ids_with_index]
    return sorted_data


# Main testing function
def test_sorting(num_elements=2000):
    global data
    # Number of times to run each sort for averaging
    num_runs = 1000

    # Generate the data
    data = generate_data(num_elements)
    start = time.time()
    # Measure time for lambda
    lambda_time = timeit.Timer("sort_with_lambda(data.copy())", globals=globals(), timer=time.process_time).timeit(number=num_runs)
    # lambda_time = timeit.timeit(
    #     "sort_with_lambda(data.copy())", globals=globals(), number=num_runs
    # )
    avg_lambda_time = lambda_time / (num_runs / 1000)

    # Measure time for itemgetter
    itemgetter_time = timeit.Timer("sort_with_itemgetter(data.copy())", globals=globals(), timer=time.process_time).timeit(number=num_runs)
    # itemgetter_time = timeit.timeit(
    #     "sort_with_itemgetter(data.copy())", globals=globals(), number=num_runs
    # )
    avg_itemgetter_time = itemgetter_time / (num_runs / 1000)

    isolate_time = timeit.Timer("sort_by_isolating(data.copy())", globals=globals(), timer=time.process_time).timeit(number=num_runs)
    # isolate_time = timeit.timeit(
    #     "sort_by_isolating(data.copy())", globals=globals(), number=num_runs
    # )
    avg_isolate_time = isolate_time / (num_runs / 1000)
    stop = time.time()

    # print(f"Average time using lambda     : {avg_lambda_time:.6f} ms")
    # print(f"Average time using itemgetter : {avg_itemgetter_time:.6f} ms")
    # print(f"Total: {(stop - start)*1000:.6f} ms")
    return avg_lambda_time, avg_itemgetter_time, avg_isolate_time


if __name__ == "__main__":
    x = []
    lamdaTime = []
    IGtime = []
    isoTime = []
    bar = tqdm.tqdm(range(0, 1000, 10))
    for i in range(0, 1000, 10):
        bar.update(1)
        x.append(i + 2000)
        lamTim, IGTim, isoTim = test_sorting(i + 2000)
        lamdaTime.append(lamTim)
        IGtime.append(IGTim)
        isoTime.append(isoTim)
    bar.close()
    plt.plot(x, lamdaTime, label="Lambda")
    plt.plot(x, IGtime, label="Itemgetter")
    plt.plot(x, isoTime, label="sort by isolating")
    plt.xlabel("amt")
    plt.ylabel("ms")
    plt.legend()

    plt.show()
