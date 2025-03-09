import time
startTime = time.perf_counter()
currentTime = []
thrust = [5, 7, 8, 2, 5]

currentTime.append(time.perf_counter())
time.sleep(1)
currentTime.append(time.perf_counter())
time.sleep(1)
currentTime.append(time.perf_counter())
time.sleep(1)
currentTime.append(time.perf_counter())
time.sleep(1)
currentTime.append(time.perf_counter())
time.sleep(1)

value = 0
while value < len(thrust):
    print(thrust[value], ", ", round((currentTime[value] - startTime), 3), sep = '')
    value += 1