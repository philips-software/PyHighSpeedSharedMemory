import pickle
from multiprocessing import shared_memory


class MemoryInterface:
    parms = {}
    circular_mem = {}
    size_in_bytes = 0
    nr_of_memories = 0
    read_pointer = 0
    write_pointer = 0
    loaded = False

    def __init__(self, memblk=None):

        self.write_pointer = SharedInt()
        self.read_pointer = SharedInt()
        self.mem_size = SharedInt()
        self.nr_of_memories = 0
        self.use_pickle = True
        self.partial_data = bytearray(0)

        if memblk != None:
            self.load_memorybuf(memblk)

    def create_memorybuf(self, largest_object=[i for i in range(100)], nr_of_memories=10, use_pickle=True):
        """
        the memory shall always carray a pickled object
        """

        if use_pickle:
            largestbuf = pickle.dumps(largest_object)
        else:
            largestbuf = largest_object
        self.size_in_bytes = len(largestbuf)
        self.nr_of_memories = nr_of_memories
        self.use_pickle = use_pickle

        self.circular_mem = []
        setmemblks = []
        for i in range(nr_of_memories):
            shm = SharedBytes()
            memblk = shm.create_sharedobject(self.size_in_bytes)

            shv = SharedInt()
            valblk = shv.create_sharedobject()
            shv.write(0)

            self.circular_mem.append({"memory": shm, "valid": shv})
            setmemblks.append({"memory": memblk, "valid": valblk})

        if self.use_pickle:
            self.read = self.read_pickle
            self.write = self.write_pickle
        else:
            self.read = self.read_bytes
            self.write = self.write_pickle

        memblk_write = self.write_pointer.create_sharedobject()
        memblk_read = self.read_pointer.create_sharedobject()
        memblk_sib = self.mem_size.create_sharedobject()
        self.write_pointer.write(0)
        self.read_pointer.write(0)
        self.mem_size.write(self.size_in_bytes)

        parms = {"writepointer": memblk_write,
                 "readpointer": memblk_read,
                 "size_in_bytes": memblk_sib,
                 "memlist": setmemblks,
                 "use_pickle": use_pickle}

        return parms

    def load_memorybuf(self, parms):
        """
        Warning! after transfer through Process, all memmories may be larger!!
        """
        self.write_pointer.load_sharedobject(parms["writepointer"])
        self.read_pointer.load_sharedobject(parms["readpointer"])
        self.mem_size.load_sharedobject(parms["size_in_bytes"])
        self.size_in_bytes = self.mem_size.read()
        self.nr_of_memories = len(parms["memlist"])
        self.use_pickle = parms["use_pickle"]

        self.circular_mem = []
        for i in parms["memlist"]:
            shm = SharedBytes(i["memory"])
            shv = SharedInt(i["valid"])
            self.circular_mem.append({"memory": shm, "valid": shv})

        self.loaded = True

        if self.use_pickle:
            self.read = self.read_pickle
            self.write = self.write_pickle
        else:
            self.read = self.read_bytes
            self.write = self.write_bytes

    def can_read(self):

        res = self.is_valid(self.read_pointer.read())
        return res == True

    def reset_read(self):

        goal = (self.get_write_pointer() - 1 + self.nr_of_memories) % self.nr_of_memories
        while self.can_read() and self.get_read_pointer() != goal:
            self._increment_read_pointer()

        if self.can_read():
            self._increment_read_pointer()

    def read_bytes(self):

        cmd_stream = self.circular_mem[self.read_pointer.read()]["memory"].read()

        self._increment_read_pointer()

        return cmd_stream

    def _increment_read_pointer(self):

        self.circular_mem[self.read_pointer.read()]["valid"].write(0)
        self.read_pointer.write((self.read_pointer.read() + 1) % self.nr_of_memories)

    def read_pickle(self):

        mem = self.circular_mem[self.read_pointer.read()]["memory"].read()
        cmd_stream = pickle.loads(mem)

        self._increment_read_pointer()

        return cmd_stream

    def get_read_pointer(self):
        return self.read_pointer.read()

    def get_write_pointer(self):
        return self.write_pointer.read()

    def get_size_in_bytes(self):
        return self.size_in_bytes

    def get_number_of_memories(self):
        return self.nr_of_memories

    def can_write(self):

        res = self.is_valid(self.write_pointer.read())
        return res == False

    def write_partial(self, rsp_stream):

        self.partial_data += rsp_stream

        if len(self.partial_data) > self.size_in_bytes:
            self.circular_mem[self.write_pointer.read()]["memory"].mem.buf[:self.size_in_bytes] = \
                self.partial_data[:self.size_in_bytes]

            self._increment_write_pointer()

            self.partial_data = self.partial_data[self.size_in_bytes:]

        return len(self.partial_data)

    def _increment_write_pointer(self):

        self.circular_mem[self.write_pointer.read()]["valid"].write(self.size_in_bytes)
        self.write_pointer.write((self.write_pointer.read() + 1) % self.nr_of_memories)

    def write_bytes(self, rsp_stream):

        if len(self.circular_mem) == 0:
            return

        bufsize = len(rsp_stream)

        if bufsize > self.size_in_bytes:
            msg = f"too large: {bufsize} but only {self.size_in_bytes}"
            raise ValueError(msg)

        self.circular_mem[self.write_pointer.read()]["memory"].write(rsp_stream)
        self.circular_mem[self.write_pointer.read()]["valid"].write(bufsize)

        self.write_pointer.write((self.write_pointer.read() + 1) % self.nr_of_memories)

        return bufsize

    def write_pickle(self, rsp_stream):

        if len(self.circular_mem) == 0:
            return

        buf = pickle.dumps(rsp_stream)
        bufsize = len(buf)

        if bufsize > self.size_in_bytes:
            msg = f"too large: {len(buf)} but only {self.size_in_bytes}"
            raise ValueError(msg)

        self.circular_mem[self.write_pointer.read()]["memory"].write(buf)
        self.circular_mem[self.write_pointer.read()]["valid"].write(bufsize)

        self.write_pointer.write((self.write_pointer.read() + 1) % self.nr_of_memories)

        return bufsize

    def is_valid(self, index):
        if len(self.circular_mem) == 0:
            return False

        bufsize = self.circular_mem[index]["valid"].read()
        return bufsize > 0

    def get_fullness(self):

        writepointer = self.get_write_pointer()
        readpointer = self.get_read_pointer()
        fill = (writepointer - readpointer + self.nr_of_memories) % self.nr_of_memories
        if fill == 0 and self.can_write() == False:
            fill = self.nr_of_memories

        return 100 * fill // self.nr_of_memories

    def cleanup(self):

        if len(self.circular_mem) == 0:
            return

        for mem in self.circular_mem:
            mem["memory"].cleanup()
            mem["valid"].cleanup()

        self.circular_mem = {}
        self.mem_size.write(0)


class SharedBytes:
    size_in_bytes = 0
    loaded = False
    mem = None

    def __init__(self, memblk=None):

        if memblk != None:
            self.load_sharedobject(memblk)

    def create_sharedobject(self, size):

        self.size_in_bytes = size
        self.rsp_stream = bytearray(self.size_in_bytes)

        self.mem = shared_memory.SharedMemory(create=True, size=self.size_in_bytes)

        self.memblk = {"size": self.size_in_bytes, "memory": self.mem}
        self.loaded = False

        return self.memblk

    def load_sharedobject(self, memblk):

        self.size_in_bytes = memblk["size"]
        self.mem = memblk["memory"]
        self.rsp_stream = bytearray(self.size_in_bytes)
        self.loaded = True

    def write(self, rsp_stream):

        if self.mem == None:
            raise ValueError(f"Error: no object loaded")

        bufsize = len(rsp_stream)

        if bufsize > self.size_in_bytes:
            raise ValueError(f"too large: {len(rsp_stream)} but only {self.size_in_bytes}")

        self.mem.buf[:bufsize] = rsp_stream[:bufsize]
        return True

    def read(self):

        if self.mem == None:
            raise ValueError(f"Error: no object loaded")

        self.rsp_stream[:] = self.mem.buf[:self.size_in_bytes]

        return self.rsp_stream

    def cleanup(self):

        if self.mem == None:
            return

        self.mem.close()
        if not self.loaded:
            self.mem.unlink()

        self.mem = None
        self.loaded = False


class SharedInt:
    intsize = 8

    def __init__(self, num=None):
        self.sharedbytes = SharedBytes(num)

    def create_sharedobject(self):
        self.memblk = self.sharedbytes.create_sharedobject(8)
        return self.memblk

    def load_sharedobject(self, memblk):
        self.sharedbytes.load_sharedobject(memblk)

    def read(self):
        bb = self.sharedbytes.read()
        res = int.from_bytes(bb, byteorder="little", signed=True)
        return res

    def write(self, num):
        bb = num.to_bytes(SharedInt.intsize, "little", signed=True)
        self.sharedbytes.write(bb)

    def cleanup(self):
        self.sharedbytes.cleanup()


class SharedBool:

    def __init__(self, mem=None):
        self.sharedbytes = SharedBytes(mem)

    def create_sharedobject(self):
        self.memblk = self.sharedbytes.create_sharedobject(1)
        return self.memblk

    def load_sharedobject(self, memblk):
        self.sharedbytes.load_sharedobject(memblk)

    def read(self):
        bb = self.sharedbytes.read()
        res = bool.from_bytes(bb, byteorder="little")
        return res

    def write(self, isnum):
        bb = isnum.to_bytes(1, "little")
        self.sharedbytes.write(bb)

    def cleanup(self):
        self.sharedbytes.cleanup()


class SharedString:
    intsize = 4  # 8bits/bytes -> 32 bits
    maxval = 2 ** (intsize * 8) - 1  # 2**32 -1 ... 1GB large enough?

    def __init__(self, num=None):

        self.sharedbytes = SharedBytes(num)
        self.len = 0

    def create_sharedobject(self, maxlength):

        if maxlength <= SharedString.intsize:
            msg = f"maxlength must be larger than {SharedString.intsize} to support 1 character\n" \
                  f" because its length is being tracked by the first {SharedString.intsize} bytes"
            raise ValueError(msg)

        if maxlength > SharedString.maxval:
            msg = f"maxlength must be smaller than {SharedString.maxval}\n " \
                  f"so that its length can be tracked by the first {SharedString.intsize} bytes"
            raise ValueError(msg)

        self.memblk = self.sharedbytes.create_sharedobject(maxlength + SharedString.intsize)
        return self.memblk

    def load_sharedobject(self, memblk):

        self.sharedbytes.load_sharedobject(memblk)

    def read(self):

        bb = self.sharedbytes.read()
        strlen = int.from_bytes(bb[:SharedString.intsize], byteorder="little", signed=True)
        res = bb[SharedString.intsize:].decode("utf-8").strip("\0")
        resstripped = res[:strlen]
        return resstripped

    def write(self, val):

        strlen = len(val)
        nn = strlen.to_bytes(SharedString.intsize, "little", signed=True)
        bb = nn + val.encode("utf-8")
        self.sharedbytes.write(bb)

    def cleanup(self):

        self.sharedbytes.cleanup()
