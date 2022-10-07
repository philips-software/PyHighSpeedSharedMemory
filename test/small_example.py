import time
from multiprocessing import Process

from memory_interface import SharedString

INITIAL_STRING = "Hello"
ANSWER = "From afar"


def runningstr(memblk):
    # jump start a local version:
    localstr = SharedString(memblk)
    first_string = localstr.read()
    assert first_string == INITIAL_STRING
    localstr.write(ANSWER)  # give an answer
    print(f"From afar read {first_string} and is sending {ANSWER}")


def Initialize():
    sharedstring = SharedString()
    memblk = sharedstring.create_sharedobject(200)  # the shared string will be 200 charactgers in length

    sharedstring.write(INITIAL_STRING)  # initialize it (must be less than 200)

    proc = Process(target=runningstr, args=[memblk])  # passes the memblk
    proc.start()

    busy = True
    while busy:
        answer = sharedstring.read()
        if answer == INITIAL_STRING:
            print("Waiting....")
            time.sleep(1)
        else:
            busy = False

    assert answer == ANSWER
    print(f"In main process read: <{answer}>")

    proc.join()
    sharedstring.cleanup()


if __name__ == "__main__":
    Initialize()
