import random, time

while True:
    temp = random.randint(160, 220)
    print(temp)
    with open("w1_slave", "w") as f:
        f.writelines(["50 01 80 80 1f ff 80 80 d2 : crc=d2 YES\n",
                     f"50 01 80 80 1f ff 80 80 d2 t={temp}00"])
    time.sleep(1)
