import logging
import pickle
import time
from multiprocessing import Process

from generic_tester import tst_runner
from memory_interface import MemoryInterface, SharedBool

logging.basicConfig(level=logging.INFO)


def needparms(memblk):
    logging.info(" in memory")
    m2 = MemoryInterface()
    m2.load_memorybuf(memblk)
    logging.info("finished")

    m2.cleanup()

    return True


def canbeprocessed():
    logging.info("validate that it can be multipprocessed")
    memsize = 20
    nrmem = 5
    m1 = MemoryInterface()
    memblk = m1.create_memorybuf(memsize, nrmem)

    pok = Process(target=needparms, args=(memblk,))
    pok.start()
    pok.join()

    m1.cleanup()

    logging.info("validation success")

    return True


def testbasics():
    largest_number = 100
    largest = [i for i in range(largest_number)]
    memsize = len(pickle.dumps(largest))
    nrmem = 5
    m1 = MemoryInterface()
    m1.create_memorybuf(largest, nrmem)

    m2s = MemoryInterface()
    memblk = m2s.create_memorybuf(largest, nrmem)

    m2 = MemoryInterface()
    m2.load_memorybuf(memblk)

    logging.info("for both m2 as mi must hold the following:")
    for mi in [m1, m2]:

        assert mi.get_read_pointer() == 0
        assert mi.get_write_pointer() == 0
        assert mi.get_size_in_bytes() == memsize

        logging.info("validate that, at start, the number and that all are empty:")
        for i in range(nrmem):
            num = mi.is_valid(i)
            logging.debug(f"{i}, {num}")
            assert 0 == num

        logging.info("validate that the read and write pointers are zero:")
        assert mi.get_read_pointer() == 0
        assert mi.get_write_pointer() == 0
        assert mi.get_fullness() == 0

        logging.info("validate that, at start, you can write but can't read:")
        assert mi.can_read() == False
        assert mi.can_write() == True

        logging.info("can read is the same asa is_valid")
        assert mi.can_read() == mi.is_valid(mi.get_read_pointer())

        logging.info("Validate that what you write you can then read")

        towrite = [i for i in range(largest_number // 2)]
        towritelen = len(pickle.dumps(towrite))
        written = mi.write(towrite)
        assert towritelen == written
        logging.info("validate that the fullness is 1")
        a = mi.get_fullness()

        assert 1 * 100 // nrmem == a

        logging.info("Validate that the reader can now read what was written")
        assert mi.get_write_pointer() == 1
        assert mi.get_read_pointer() == 0
        assert True == mi.can_read()
        toread = mi.read()
        assert toread == towrite
        logging.info("validate that the fullness is 0")
        assert 0 == mi.get_fullness()

        logging.info("Validate that the reader and writer are as, like before ")
        assert mi.can_read() == False
        assert mi.can_write() == True

        logging.info("Validate that if you write too much only the min will be read")
        startwrtptr = mi.get_write_pointer()
        towrite2 = [i for i in range(largest_number + 1)]
        logging.info(f"too much is now {len(towrite)} while only {memsize} can")
        try:
            written = mi.write(towrite2)
            ok = False
        except:
            ok = True

        assert ok == True
        assert startwrtptr == mi.get_write_pointer()
        logging.info(" ... and the write index is still the same")
        logging.info("now writing something else: bytestream")

        base = [i for i in range(largest_number)]
        towritelen = len(pickle.dumps(base))
        written = mi.write(base)
        assert towritelen == written

        logging.info("Validate that the reader can now read the bytearray was written")
        assert True == mi.can_read()
        toread = mi.read()
        assert base == toread

        logging.info("validate that we now have no valid elements")
        for i in range(nrmem):
            logging.debug(f"{i}, {mi.is_valid(i)}")
            assert mi.is_valid(i) == False

        logging.info("now we are going around and fill all of the elements")
        for i in range(nrmem):
            if mi.can_write():
                towrite = [j for j in range(largest_number // 4)]
                mi.write(towrite)
            else:
                raise ValueError(f"could not write to {i}")

        assert mi.can_write() == False
        logging.info("...and validated that all is now full")
        logging.info("validate that the fullness is max")
        assert mi.get_number_of_memories() * 100 // nrmem == mi.get_fullness()
        logging.info("so now  all can be read")

        towrite = [j for j in range(largest_number // 4)]
        for i in range(nrmem):
            if mi.can_read():
                rec = mi.read()
                assert rec == towrite
            else:
                raise ValueError(f"could not read from {i}")

        # because each are unique:
        mi.cleanup()

    return True


def readnumbers(memblk, ms, membusy):
    mi = MemoryInterface(memblk)
    busy = SharedBool(membusy)

    i = 0
    nrwait = 0
    towrite = [1]
    while busy.read():

        while not mi.can_read():
            nrwait += 1

        rec = mi.read()
        assert rec == [i]
        i += 1

    mi.cleanup()
    return True


def writenumbers(memblk, ms, membusy):
    mi = MemoryInterface(memblk)
    busy = SharedBool(membusy)

    assert ms == mi.get_size_in_bytes()
    buflen = mi.get_size_in_bytes()
    assert ms <= buflen, f"ms={ms} may not be larger than buflen={buflen}"
    logging.info(f"ms may not be larger than buflen: ms={ms} <= buflen={buflen}")

    i = 0
    nrwait = 0
    while busy.read():

        while not mi.can_write():
            nrwait += 1

        mi.write([i])
        i += 1

    mi.cleanup()
    return True


def testnumbers():
    largest_size = 100
    largest = [i for i in range(largest_size)]
    memsize = len(pickle.dumps(largest))
    nrmem = 5
    m1 = MemoryInterface()
    memblk = m1.create_memorybuf(largest, nrmem)
    busy = SharedBool()
    membusy = busy.create_sharedobject()
    busy.write(True)

    p1 = Process(target=writenumbers, args=(memblk, memsize, membusy))
    p2 = Process(target=readnumbers, args=(memblk, memsize, membusy))

    p2.start()
    p1.start()

    count = 0
    while count < 100:
        logging.debug(f"{count}: {m1.get_fullness()}, {m1.get_read_pointer()}, {m1.get_write_pointer()}, ")
        count += 1
        time.sleep(0.1)
    busy.write(False)

    p1.join()
    p2.join()

    logging.info("now also in process")

    m1.cleanup()

    return True


def test_read_reset():
    logging.info(f'test_read_reset')

    largest= [i for  i in range(2000)]
    nrmem = 10

    m2s = MemoryInterface()
    memblk = m2s.create_memorybuf(largest, nrmem)

    m2 = MemoryInterface()
    m2.load_memorybuf(memblk)

    assert nrmem == m2s.get_number_of_memories()

    pos = m2s.get_write_pointer()
    logging.debug(f"writepointer : {pos}")

    assert pos == 0

    while m2s.can_write():
        m2s.write(largest)

    pos = m2s.get_write_pointer()
    logging.debug(f"writepointer : {pos}")

    assert m2s.can_write() == False

    assert pos == 0

    pos = m2.get_read_pointer()
    logging.debug(f"readponter = {pos}")

    m2.reset_read()

    assert False == m2.can_read()

    pos = m2.get_read_pointer()
    logging.debug(f"readponter = {pos}")

    assert pos == 0

    # now the buffer is empty, so can read again
    for i in range(nrmem // 2):
        assert m2s.can_write()
        m2s.write(largest)

    assert m2s.can_write()

    pos = m2s.get_write_pointer()
    logging.debug(f"writepointer : {pos}")
    assert pos == nrmem // 2

    # should be able to read:
    assert m2.can_read()
    pos = m2.get_read_pointer()
    logging.debug(f"readponter = {pos}")
    # still at 0
    assert pos == 0

    m2.reset_read()
    pos = m2.get_read_pointer()
    logging.debug(f"readponter before write = {pos}")

    pos = m2s.get_write_pointer()
    logging.debug(f"writepointer : {pos}")

    assert m2.can_read() == False
    assert m2.can_write() == True

    return True


def tstmain():
    tests = [canbeprocessed, testbasics, testnumbers]

    return tst_runner(tests)


if __name__ == "__main__":
    tstmain()
