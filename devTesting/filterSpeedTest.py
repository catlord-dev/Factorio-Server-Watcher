import time
import random
import string
from timeit import timeit
import ahocorasick
import numpy as np
import tqdm

# Helper function to generate random strings
def generate_random_string(length):
    return''.join(random.choices(string.ascii_letters + string.digits, k=length))
# Method 2: Using Aho-Corasick algorithm
def build_automaton(patterns):
    A = ahocorasick.Automaton()
    for pattern in patterns:
        A.add_word(pattern, pattern)
    A.make_automaton()
    return A
# Generate test data
def genData(string1Amt,string2Amt):
    string1_list = [generate_random_string(random.randint(5, 50)) for _ in range(string1Amt)]
    string2_list = [generate_random_string(random.randint(5, 20)) for _ in range(string2Amt)]

    # Method 1: Using a for loop with `in` statement
    def check_patterns_with_in(strings_list, patterns):
        results = []
        for string1 in strings_list:
            hits = {s for s in patterns if s in string1}
            results.append(hits)
        return results

    

    def check_patterns_with_automaton(strings_list, automaton):
        results = []
        for string1 in strings_list:
            hits = set()
            for end_index, original_value in automaton.iter(string1):
                hits.add(original_value)
            results.append(hits)
        return results

    # Benchmark Method 1: `in` statement
    start_time = time.time()
    results_in = check_patterns_with_in(string1_list, string2_list)
    time_in = time.time() - start_time

    # Benchmark Method 2: Aho-Corasick
    start_time = time.time()
    automaton = build_automaton(string2_list)
    
    results_aho = check_patterns_with_automaton(string1_list, automaton)
    time_aho = time.time() - start_time
    assert results_in == results_aho, "The results differ between the methods!"
    return time_in, time_aho
import matplotlib.pyplot as plt

times1 = []
times2 = []
amts = []
scale = 1000
amt = 300
bar = tqdm.tqdm(range(1000))
for i in range(1,1000):
    bar.update(1)
    tmpTime1 = []
    tmpTime2 = []
    for ii in range(10):
        inTime , ahoTime = genData(3000,i)
        tmpTime1.append(inTime)
        tmpTime2.append(ahoTime)
    times1.append(sum(tmpTime1)/len(tmpTime1)*scale)
    times2.append(sum(tmpTime2)/len(tmpTime2)*scale)
    amts.append(i)

bar.close()
plt.plot(amts, times1)
plt.plot(amts, times2)

plt.legend(["in", "aho"])

plt.xlabel("amt")
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
    tim = timeit(lambda: build_automaton(patList),  number=100)
    times.append(tim*10)
    amts.append(i)
bar.close()

slope3 , slope2,slope, intercept = np.polyfit(amts, times, 3)
lineofbestfit = np.array(amts)*(slope3**3)+np.array(amts)*(slope2**2)+slope * np.array(amts) + intercept
plt.plot(amts, times)
plt.plot(amts, lineofbestfit,label="Best Fit")
print(f"{(tim):.2f} ms per")
print(f"Total time: {time.time() - start:.4f} seconds")
plt.show()