import random, time

up = True
min = 250
max = 300
step=5
while True:
    # temp = random.randint(160, 220)
    if up:
        temp_range = range(min,max,step)
        up = False
    else:
        temp_range = range(max,min,-step)
        up = True
    for temp in temp_range:
        with open("w1_slave1", "w") as f:
            f.writelines(["50 01 80 80 1f ff 80 80 d2 : crc=d2 YES\n",
                         f"50 01 80 80 1f ff 80 80 d2 t={temp}00"])
        with open("w1_slave2", "w") as f:
            f.writelines(["50 01 80 80 1f ff 80 80 d2 : crc=d2 YES\n",
                         f"50 01 80 80 1f ff 80 80 d2 t={temp}00"])
        print(temp)

        time.sleep(5)
