import random, time
import math

up = True
t1min = 0
t1max = 140
t2min = 0
t2max = 120
step = 5
time_period = 60
while True:
    # temp = random.randint(160, 220)
    temp_range1 = range(t1min, t1max, step)
    temp_range2 = range(t2max, t2min, -step*2)


    for (temp1, temp2) in zip(temp_range1, temp_range2):
        with open("w1_slave1", "w") as f:
            t1 =  (math.sin(math.radians(temp1 * 10))  + 5)/2
            t1 = "%.2f" % t1
            t1=int(float(t1)*100)
            f.writelines(["50 01 80 80 1f ff 80 80 d2 : crc=d2 YES\n",
                          f"50 01 80 80 1f ff 80 80 d2 t={t1}00"])
            print(f'{t1} ',end="")
        with open("w1_slave2", "w") as f:
            f.writelines(["50 01 80 80 1f ff 80 80 d2 : crc=d2 YES\n",
                          f"50 01 80 80 1f ff 80 80 d2 t={temp2}00"])
            print(f'{temp2}')

        time.sleep(1)

