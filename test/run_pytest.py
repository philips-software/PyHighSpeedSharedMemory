#!/usr/bin/env python3

"""The script is deliberately in Python, so it is cross-platform.

It runs all unit test of the testframework and checks if they all pass
"""

import os
import pytest
import time


TESTDIR = os.path.dirname(__file__)

print(f"Tests are located in: {TESTDIR}")

def run_pytest():
    """
    run the pytests
    """
    result = pytest.main(["-v", "--junit-xml", "test_results.xml", TESTDIR])

    assert result == 0


if __name__ == "__main__":
    run_pytest()

