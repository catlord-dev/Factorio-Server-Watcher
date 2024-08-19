

import math


dis = 1
power = 4

for i in range(28):
    print(f"{i}/27 - {(1-(dis/(2*power)))*(i/27)}")
    
vel = .4803299332093225
print()
print(f"{math.ceil(16/vel)} tnt")
print(f"{math.ceil(16/vel)*vel} Vel")
print()
print(f"{math.ceil(20/vel)} tnt")
print(f"{math.ceil(20/vel)*vel} Vel")
print()
print(f"{math.ceil(100/vel)} tnt")
print(f"{math.ceil(100/vel)*vel} Vel")

print()
chunks = 13
wantVel = (chunks*16)
print(f"{math.ceil(wantVel/vel)} tnt")
print(f"{math.ceil(wantVel/vel)*vel} Vel")

print()
startvel = math.ceil(100/vel)*vel
acc = 0
drag = .09
for i in range(15):
    print(f"{i} - {(startvel*(1-drag)**i)-(acc* ((1-(1-drag)**i)/(drag))):.2f}")