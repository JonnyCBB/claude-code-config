#!/usr/bin/env python3
"""The test runner's own exit code is a contract, so assert on it.

run-tests.sh exists to stop a check that cannot fail, and it was one: setting its
final line to `exit 0` left it printing "Results: 1 of 5 module(s) failed." while
exiting 0, and nothing in the repository noticed. README documented
`EXPECT_BOOTSTRAP_RED=1 ... # must exit non-zero` as a MANUAL step, so the only
thing checking the checker was a human remembering to look.

These tests run a COPY of the runner in a temp directory, so there is no
recursion: the copy only ever sees the bootstrap module placed beside it.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
RUNNER = TESTS_DIR / "run-tests.sh"
BOOTSTRAP = TESTS_DIR / "test_bootstrap.py"


class HarnessContractTest(unittest.TestCase):
    def _sandbox(self, with_bootstrap=True):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        shutil.copy(RUNNER, Path(tmp) / "run-tests.sh")
        if with_bootstrap:
            shutil.copy(BOOTSTRAP, Path(tmp) / "test_bootstrap.py")
        return Path(tmp)

    def _run(self, sandbox, env=None):
        return subprocess.run(
            ["bash", str(sandbox / "run-tests.sh")],
            capture_output=True,
            text=True,
            env=env,
        )

    def test_a_passing_suite_exits_zero(self):
        done = self._run(self._sandbox())
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_a_failing_module_makes_the_runner_exit_nonzero(self):
        # The property README documents as a manual step. Asserted here so the
        # checker cannot silently stop checking.
        done = self._run(
            self._sandbox(), env={"EXPECT_BOOTSTRAP_RED": "1", "PATH": "/usr/bin:/bin"}
        )
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("FAIL", done.stdout)

    def test_finding_no_test_modules_is_a_failure_not_a_pass(self):
        done = self._run(self._sandbox(with_bootstrap=False))
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("NO TEST MODULES FOUND", done.stdout)

    def test_the_exit_code_is_the_number_of_failing_modules(self):
        sandbox = self._sandbox()
        second = sandbox / "test_second_failure.py"
        second.write_text(
            "import sys, unittest\n"
            "class T(unittest.TestCase):\n"
            "    def test_fails(self):\n"
            "        self.fail('deliberate')\n"
            'if __name__ == "__main__":\n'
            "    unittest.main()\n"
        )
        done = self._run(
            sandbox, env={"EXPECT_BOOTSTRAP_RED": "1", "PATH": "/usr/bin:/bin"}
        )
        self.assertEqual(done.returncode, 2, done.stdout)


if __name__ == "__main__":
    unittest.main()
