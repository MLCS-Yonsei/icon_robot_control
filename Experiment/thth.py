import threading
import time
def threadOne(a):
    while True:
        time.sleep(1)
        print(a)

def threadTwo(a):
    while True:
        time.sleep(2)
        print(100 - a)


t1 = threading.Thread(target=threadOne, args=(5,)).start()
t2 = threading.Thread(target=threadTwo, args=(5,)).start()

