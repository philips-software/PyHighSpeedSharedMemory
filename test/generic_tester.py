import os
import sys
import time
import traceback


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def tst_runner(tests):
    res = []
    times = []
    nrfailed = 0
    nrsuccess = 0
    maxnamelength = 5
    timestart = time.time()
    for function_under_test in tests:
        substart = time.time()
        try:
            function_under_test()
            res.append("Success")
            nrsuccess += 1
        except Exception as inst:
            print(traceback.format_exc(), file=sys.stderr)
            # print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno),
            #       type(inst).__name__, inst, file=sys.stderr)
            # print(f"{i.__name__} failed: {inst}", file=sys.stderr)
            res.append("Failed")
            nrfailed += 1
        subtime = time.time() - substart
        times.append(subtime)
        if len(function_under_test.__name__) > maxnamelength:
            maxnamelength = len(function_under_test.__name__)
    timeend = time.time()
    prettygood = f"{{:{maxnamelength}}} :{bcolors.OKGREEN}{{:s}}{bcolors.ENDC}, {{:0.3f}} "
    prettyfail = f"{{:{maxnamelength}}} :{bcolors.FAIL}{{:s}}{bcolors.ENDC}, {{:0.3f}} "

    print("Result Summary:", file=sys.stderr)
    for nr, i in enumerate(res):
        if res[nr] == "Success":
            msg = prettygood.format(tests[nr].__name__, res[nr], times[nr])
        else:
            msg = prettyfail.format(tests[nr].__name__, res[nr], times[nr])
        print(msg, file=sys.stderr)

    if nrfailed == 0:
        print(
            f"Ran {nrfailed + nrsuccess} tests in {timeend - timestart:0.3f}sec, {bcolors.OKGREEN}ALL OK{bcolors.ENDC}",
            file=sys.stderr)
    else:
        print(
            f"Ran {nrfailed + nrsuccess} tests in {timeend - timestart:0.3f}sec, {bcolors.FAIL}{nrfailed} failed{bcolors.ENDC}",
            file=sys.stderr)

    msg = {"module": os.path.basename(__file__), "total": nrfailed + nrsuccess,
           "Fails": nrfailed, "results": res, "tests": tests}
    return msg
