#!/usr/bin/env python3
"""Bootstrap check: proves hooks/tests/run-tests.sh can report a failure.

This looks like a test of unittest itself, which docs/test-writing.md rejects.
It is not: the thing under test is run-tests.sh's loop, its module counting and
its exit-code accumulation, which are this repo's code. Set
EXPECT_BOOTSTRAP_RED=1 and the runner must exit non-zero.
"""

import os
import unittest


class BootstrapTest(unittest.TestCase):
    def test_harness_reports_failure_when_asked(self):
        if os.environ.get("EXPECT_BOOTSTRAP_RED") == "1":
            self.fail("deliberate failure: EXPECT_BOOTSTRAP_RED=1 was set")


if __name__ == "__main__":
    unittest.main()
