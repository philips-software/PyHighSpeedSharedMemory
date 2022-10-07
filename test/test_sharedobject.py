import logging
import sys
import time
from multiprocessing import Process

from generic_tester import tst_runner
from memory_interface import SharedBytes, SharedInt, SharedBool, SharedString

FORMAT = '%(asctime)s:%(levelname)-8s:%(filename)s:%(funcName)s:%(lineno)d: %(message)s'
handlers = [logging.StreamHandler()]
logging.basicConfig(format=FORMAT, handlers=handlers, level=logging.DEBUG)


def runingstr(mem, bus):
    hh = SharedString(mem)
    busy = SharedBool(bus)
    busy.load_sharedobject(bus)

    logging.debug("starting run num process")
    logging.debug(f"{busy.read()}")
    assert busy.read() == True

    rounds = 0
    waitnr = 0
    while busy.read():
        a = hh.read()
        waitnr = 0
        while hh.read() == "Here" and busy.read():
            waitnr += 1
            logging.info(f"waiting for Here a={hh.read()}, waitnr={waitnr}, rounds={rounds}")
            time.sleep(0.1)
        logging.info(f"waiting for Here a={hh.read()}, rounds={rounds}")
        hh.write("there")
        rounds += 1
        if rounds > 10:
            busy.write(False)

    hh.cleanup()
    busy.cleanup()
    logging.debug("run process ended ")


def test_first1():
    sh = SharedBytes()

    aa = 10

    res = sh.create_sharedobject(10)

    sh.write(aa.to_bytes(aa, "little"))

    bb = sh.read()
    cc = int.from_bytes(bb, byteorder="little")
    print(cc)

    assert cc == aa

    pp = SharedBytes()
    res = pp.create_sharedobject(1)
    pp.write(bytearray([0]))

    cc = pp.read()
    print(f"now 1 ={cc}")

    assert cc == bytearray([0])

    cb = int.from_bytes(cc, byteorder="little")
    print(cb)

    sh.cleanup()

    return True


def running(mem, bus):
    hh = SharedBytes()
    hh.load_sharedobject(mem)

    busy = SharedBytes()
    busy.load_sharedobject(bus)

    logging.debug("starting run process")
    logging.debug(f"{busy.read()}")
    assert busy.read() == bytearray([0])
    expect = 1
    waitnr = 0
    while busy.read() == bytearray([0]):
        ab = hh.read()
        a = int.from_bytes(ab, byteorder="little")

        logging.info(f"waiting for even a={a}, waitnr={waitnr}")
        waitnr = 0
        while a % 2 == 0:
            waitnr += 1
            ab = hh.read()
            a = int.from_bytes(ab, byteorder="little")

        if a != expect:
            issue = f"ERROR read {a}, expected {expect}"
            logging.error(issue)
            raise Exception(issue)
        else:
            expect += 2
        a += 1
        hh.write(a.to_bytes(8, "little"))

    hh.cleanup()
    busy.cleanup()
    logging.debug("run process ended ")


def test_process():
    logging.debug("going into process")
    hh = SharedBytes()
    mem = hh.create_sharedobject(10)

    busy = SharedBytes()
    bus = busy.create_sharedobject(1)
    busy.write(bytearray([0]))
    logging.info(f"{busy.read()}")
    assert busy.read() == bytearray([0])

    poc = Process(target=running, args=(mem, bus))
    poc.start()
    time.sleep(0.001)

    expect = 0
    waitnr = 0
    while busy.read() == bytearray([0]):
        ab = hh.read()
        a = int.from_bytes(ab, byteorder="little")
        logging.info(f"waiting for odd a={a}, waitnr={waitnr}")
        waitnr = 0
        while a % 2 == 1:
            waitnr += 1
            ab = hh.read()
            a = int.from_bytes(ab, byteorder="little")

        if a != expect:
            issue = f"ERROR read {a}, expected {expect}"
            logging.error(issue)
            raise Exception(issue)
        else:
            expect += 2

        a += 1
        hh.write(a.to_bytes(8, "little"))

        if a > 10:
            busy.write(bytearray([1]))

    poc.join()
    hh.cleanup()
    busy.cleanup()

    return True


def runingtight(mem, bus):
    hh = SharedBytes()
    hh.load_sharedobject(mem)

    busy = SharedBytes()
    busy.load_sharedobject(bus)

    logging.debug("starting run tight process")
    logging.debug(f"{busy.read()}")
    assert busy.read() == bytearray([0])
    expect = 1
    waitnr = 0
    while busy.read() == bytearray([0]):
        ab = hh.read()
        a = int.from_bytes(hh.read(), byteorder="little")

        logging.info(f"waiting for even a={a}, waitnr={waitnr}")
        waitnr = 0
        while int.from_bytes(hh.read(), byteorder="little") % 2 == 0:
            waitnr += 1
        if a != expect:
            issue = f"ERROR read {a}, expected {expect}"
            logging.error(issue)
            raise Exception(issue)
        else:
            expect += 1
        a += 1
        hh.write(a.to_bytes(8, "little"))

    hh.cleanup()
    busy.cleanup()
    logging.debug("run  tight process ended ")


def test_processtight():
    logging.debug("going into tight process")
    hh = SharedBytes()
    mem = hh.create_sharedobject(10)

    busy = SharedBytes()
    bus = busy.create_sharedobject(1)
    busy.write(bytearray([0]))
    logging.info(f"{busy.read()}")
    assert busy.read() == bytearray([0])

    poc = Process(target=runingtight, args=(mem, bus))
    poc.start()
    time.sleep(0.001)
    expect = 0
    waitnr = 0
    while busy.read() == bytearray([0]):
        ab = hh.read()
        a = int.from_bytes(ab, byteorder="little")

        logging.info(f"waiting for odd a={a}, waitnr={waitnr}")
        waitnr = 0
        while int.from_bytes(hh.read(), byteorder="little") % 2 == 1:
            waitnr += 1

        if a != expect:
            issue = f"ERROR read {a}, expected {expect}"
            logging.error(issue)
            raise Exception(issue)
        else:
            expect += 1
        a += 1
        hh.write(a.to_bytes(8, "little"))

        if a > 10:
            busy.write(bytearray([1]))

    poc.join()
    hh.cleanup()
    busy.cleanup()

    logging.info("tigh processes ended")

    return True


def runingnum(mem, bus):
    hh = SharedInt()
    hh.load_sharedobject(mem)

    busy = SharedInt()
    busy.load_sharedobject(bus)

    logging.debug("starting run num process")
    logging.debug(f"{busy.read()}")
    assert busy.read() == 0

    expect = 1
    waitnr = 0
    while busy.read() == 0:
        a = hh.read()

        logging.info(f"waiting for even a={a}, waitnr={waitnr}")
        waitnr = 0
        while hh.read() % 2 == 0:
            waitnr += 1

        if a != expect:
            issue = f"ERROR read {a}, expected {expect}"
            logging.error(issue)
            raise Exception(issue)
        else:
            expect += 1
        a += 1
        hh.write(a)

    hh.cleanup()
    busy.cleanup()
    logging.debug("run process ended ")


def test_processnum():
    logging.debug("going into  process num")
    hh = SharedInt()
    mem = hh.create_sharedobject()

    busy = SharedInt()
    bus = busy.create_sharedobject()
    busy.write(0)
    hh.write(0)
    logging.info(f"{busy.read()}")
    assert busy.read() == 0
    assert hh.read() == 0

    poc = Process(target=runingnum, args=(mem, bus))
    poc.start()
    time.sleep(0.001)
    expect = 0
    waitnr = 0
    while busy.read() == 0:
        a = hh.read()
        logging.info(f"waiting for odd a={a}, waitnr={waitnr}")
        waitnr = 0
        while hh.read() % 2 == 1:
            waitnr += 1

        if a != expect:
            issue = f"ERROR read {a}, expected {expect}"
            logging.error(issue)
            raise Exception(issue)
        else:
            expect += 1
        a += 1
        hh.write(a)

        if a > 10:
            busy.write(1)

    poc.join()
    hh.cleanup()
    busy.cleanup()

    logging.info("num process ended")

    return True


def test_startbytes():
    bb = SharedBytes()
    mem = bb.create_sharedobject(1)
    bb.write(bytearray([3]))
    aa = SharedBytes(mem)
    cc = aa.read()
    assert cc == bytearray([3])
    print(cc)

    return True


def test_bool():
    bb = SharedBool()
    mem = bb.create_sharedobject()
    bb.write(False)
    assert bb.read() == False

    b2 = SharedBool(mem)
    assert b2.read() == False

    print(f"bool : {b2.read()}")

    return True


def test_ints():
    bb = SharedInt()
    memb = bb.create_sharedobject()
    for i in [3, -3, 0, 2 ** 8 - 1]:
        bb.write(i)
        aa = bb.read()
        assert aa == i, f"{i} but {aa}"


def test_int():
    bb = SharedInt()
    memb = bb.create_sharedobject()
    bb.write(3)
    assert bb.read() == 3

    print(bb.read())

    aa = SharedInt(memb)
    assert aa.read() == 3

    cc = SharedInt()
    memc = cc.create_sharedobject()
    cc.write(-1)
    assert cc.read() == -1, f"-1 expected, {cc.read()} received"

    dd = SharedInt(memc)
    assert dd.read() == -1

    largestint = sys.maxsize
    smallestint = -sys.maxsize - 1

    cc.write(largestint)
    assert dd.read() == largestint

    dd.write(smallestint)
    assert cc.read() == smallestint

    return True


def test_string():
    res = True

    ss = SharedString()
    ss.create_sharedobject(10)
    inp = "hello"
    ss.write(inp)
    rr = ss.read()
    rrb = rr.encode()
    inpb = inp.encode()
    inp2 = inpb.decode()
    logging.info(f"rrlen ={len(rrb)}, inpdlen = {len(inpb)}")
    logging.info(f"hello?=={rr}")
    logging.info(f"inplen = {len(inp)}, outlen={len(rr)}")

    if rr != inp:
        logging.error(f"{inp} is not equal to {rr}")
        res = False

    if inp2 != rr:
        logging.error(f"{inp2} is not equal to {rr}")
        res = False

    assert inp2 == rr
    assert rr == inp

    return res


def test_processstring():
    logging.debug("going into  process num")
    hh = SharedString()
    mem = hh.create_sharedobject(20)

    busy = SharedBool()
    bus = busy.create_sharedobject()
    busy.write(True)
    hh.write("there")
    logging.info(f"{busy.read()}")
    assert busy.read() == True
    assert hh.read() == "there"

    poc = Process(target=runingstr, args=(mem, bus))
    poc.start()
    time.sleep(0.001)

    waitnr = 0
    rounds = 0
    while busy.read():
        a = hh.read()
        waitnr = 0
        while hh.read() == "there" and busy.read():
            waitnr += 1
            logging.info(f"waiting for there a={hh.read()}, waitnr={waitnr}, rounds={rounds}")
            time.sleep(0.1)
        logging.info(f"waiting for there a={hh.read()}, rounds={rounds}")
        hh.write("Here")
        rounds += 1
        if rounds > 1:
            busy.write(False)

    poc.join()
    hh.cleanup()
    busy.cleanup()

    logging.info("num process ended")

    return True


def test_shared_string_basic():
    logging.debug("going to test handovers")
    hh = SharedString()
    mem = hh.create_sharedobject(16)
    for i in ["Hello", "HiLonger", "", "Langerstring", "a", ]:
        hh.write(i)
        rr = hh.read()
        assert rr == i, f"<{i}> was written but <{rr}> found"

    try:
        hh.write("0123456789ABCDEFG")
        raise OverflowError("ERROR")
    except Exception as inst:
        logging.info(f"OK : <{inst}>")
        assert f"{inst}" != "ERROR", "String was too long"

    tob = "0123456789ABCDEF".encode("utf-8")
    ll = len(tob)
    assert ll == 16
    hh.write("0123456789ABCDEF")


def test_shared_string():
    logging.debug("going to test larger strings")
    hh = SharedString()
    mem = hh.create_sharedobject(1000)
    for i in ["Hello", "HiLonger", "", "Langerstring", "a",
              "Very long \u20ac String \u1234 to test with spaces special characters"]:
        hh.write(i)
        rr = hh.read()
        assert rr == i, f"<{i}> was written but <{rr}> found"

    try:
        aa = f"{0:256d}"
        logging.info(f"{len(aa)}")
        hh = SharedString()
        mem = hh.create_sharedobject(4)
        raise Exception("Should have raised a ValueError:Size too Small")
    except ValueError as inst:
        logging.info(inst)

    try:
        hh = SharedString()
        mem = hh.create_sharedobject(SharedString.maxval + 1)
        raise Exception("Should have raised a ValueError: string size too long")
    except ValueError as inst:
        logging.info(inst)

    shorter = 20
    form = f"{{:{shorter + 1}d}}"
    aa = form.format(0)
    logging.info(f"{len(aa)}")
    hh = SharedString()

    mem = hh.create_sharedobject(shorter)
    try:
        hh.write(aa)
        raise Exception("Should be an ValueError: string too long")
    except ValueError as inst:
        logging.info(inst)


def tstmain():
    tests = [test_first1, test_startbytes, test_process, test_processtight,
             test_processnum, test_int, test_ints, test_bool, test_string,
             test_processstring, test_shared_string_basic, test_shared_string]

    return tst_runner(tests)


if __name__ == "__main__":
    tstmain()
