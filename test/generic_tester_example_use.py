import logging

from handy_modules.generic_tester import test_runner
import logging

from handy_modules.generic_tester import test_runner

FORMAT = '%(asctime)s:%(levelname)-8s:%(filename)s:%(funcName)s:%(lineno)d: %(message)s'
handlers = [logging.StreamHandler()]
logging.basicConfig(format=FORMAT, handlers=handlers, level=logging.DEBUG)


def example_test():
    logging.info("Example Success")


def example_fail():
    logging.info("Failure via exception, this is an example of a failing test")

    msg = "Failing"
    raise Exception(msg)


def testmain():
    tests = [example_test, example_fail]

    return test_runner(tests)


if __name__ == "__main__":
    testmain()
