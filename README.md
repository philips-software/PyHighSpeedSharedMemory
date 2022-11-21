# PyHighSpeedSharedMemory

This repository is for the package: memory_interface.
This package contains the classes by which high speed data can be exchanged between two processes. 

The basic concept is to have two classes of the same type, exchanging data with each other at high speeds, 
each running in a different process. In Python it is not possible to distribute an initialized class between
two processes. For this reason, what is distributed are Python Dictionaries that contain the "state" of the class 
instead of the class itself. So on one size, a given class is initialized and it passes its state to 
an uninitialized version of that same class which has been launched in a different process. In the state
of both classes is a pointer to the same multiprocessing.shared_memory.Sharedmemory block.

Python's Shared memory https://docs.python.org/3/library/multiprocessing.shared_memory.html
encapsulates semaphores, so the read and write actions to a shared memory, written by a user
does not contain any checks; it can be read and written to as if it was a local variable. 

This repository contains classes that wrap the Shared memory class and contain interfaces to 
pass the classes initialized Shared memory to a class of the same type. 

There are classes to exchange primitive types of data:
- class SharedBytes
- class SharedInt
- class SharedBool
- class SharedString

And class MemoryInterface, which is a circular memory of user-defined data chunks. 
This circular memory structure has its own "semaphores", which a user must use, to
ensure that data is not overwritten and that only valid data is read. 

All of the classes SharedXXX share the basic structure:

````python
     class xxx:
       def __init__(self, memblk=None):
       # this gives the possiblit to quickly initiize this class with the state in "memblk"

       def create_sharedobject(self, *kwargs) -> object:
       # this method creates a shared object; the classes "states" to be exchanged
       # this returns the classes "state"

       def load_sharedobject(self, memblk):
       #this method loads the state contained in memblk

       def read(self):
       # this method performs a read of the shared object and returns it

       def write(self, num):
       # this method writes num to the shared object.
       # it will throw a ValueError if it is to large or is None

       def cleanup(self):
       # to be clalled by the creator of this class
````
Their typical Use: The initiator creates the shared object and then passes it on to a process
```python
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
```
 
The class MemoryInterface has its own "semaphores", which a user can use, to
ensure that data is not overwritten and that only valid data is read. 

The "can_read"  method is to be called before the "read" method to ensure that only
valid data is read.

The "can_write" method is to be called before the "write" method to ensure that valid
data is not overwritten. 

The method "get_fullness" can be used to monitor the filling of the circular memory

````python
     class MemoryInterface:
     
       def __init__(self, memblk=None):
       # this gives the possibility to quickly initiize this class with the state in "memblk"

       def create_memorybuf(self, largest_object=[i for i in range(10)], nr_of_memories=10, use_pickle=True):
       # this method creates a shared object; the classes "states" to be exchanged
       # this returns the classes "state"
       # Must use pickel, unless largest_objest are bytes. 

       def load_memorybuf(self, memblk):
       # this method loads the state contained in memblk
       
       def can_read(self)->bool:
       # this is the semaphore. Only if True, then read may be performed

       def read(self):
       # this method performs a read of the shared object and returns it

       def can_write(self)->bool:
       # this is the semaphore: write only if this is true
       
       def write(self, num):
       # this method writes num to the shared object.
       # it will throw a ValueError if it is to large or is None

       def cleanup(self):
       # to be clalled by the creator of this class
````
