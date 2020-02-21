"""Test basic funtionality of custom_runner"""

from __future__ import absolute_import
import sys
import unittest
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch
import os.path as op

from argparse import Namespace

TEST_DIR = op.dirname(op.abspath(__file__))
sys.path.insert(0, op.abspath(op.join(op.dirname(__file__), '..')))

from custom_runner import PylintRunner, parse_args  # pylint:disable=wrong-import-position

# pylint: disable=missing-docstring
class VainuTestCase(unittest.TestCase):

    def setUp(self):
        args = Namespace(rcfile=None, thresh=9.0, allow_errors=False,
                         ignore_tests=False, keep_results=False,
                         reduce_logging=False,
                         verbosity=30, custom_path="")
        self.runner = PylintRunner(args)

    def test_wrong_fileinputs(self):
        self.assertFalse(self.runner.run_pylint('test.txt'))
        self.assertFalse(self.runner.run_pylint('not_existing.py'))

    @patch("pylint.lint.PyLinter")
    def test_handle_error(self, mock_lint):
        mock_lint.side_effect = ValueError('test')
        self.assertFalse(self.runner.run_pylint(op.join(TEST_DIR, "inputs/test_input_fail.py")))

    def test_run(self):
        fnames = [op.join(TEST_DIR, "inputs/test_input_fail.py")]
        with self.assertRaises(SystemExit) as sys_exit:
            self.runner.run(fnames)
        self.assertEqual(sys_exit.exception.code, 1)
        with self.assertRaises(SystemExit) as sys_exit:
            self.runner.run([op.join(TEST_DIR, "inputs/test_input_pass.py")])
        self.assertEqual(sys_exit.exception.code, 0)

    def test_run_diff_inputs(self):
        fnames = [op.join(TEST_DIR, "inputs/test_input_fail.py")]
        with self.assertRaises(SystemExit) as sys_exit:
            self.runner.run(fnames)
        self.assertEqual(sys_exit.exception.code, 1)
        self.runner.ignore_tests = True
        with self.assertRaises(SystemExit) as sys_exit:
            self.runner.run(fnames)
        self.assertEqual(sys_exit.exception.code, 0)
        self.runner.ignore_tests = False
        self.runner.allow_errors = True
        self.runner.thresh = -5
        with self.assertRaises(SystemExit) as sys_exit:
            self.runner.run(fnames)
        self.assertEqual(sys_exit.exception.code, 0)

    def test_keep_results(self):
        self.runner.keep_results = True
        fnames = [op.join(TEST_DIR, "inputs/test_input_fail.py")]
        with self.assertRaises(SystemExit) as sys_exit:
            self.runner.run(fnames)
        self.assertEqual(sys_exit.exception.code, 1)
        with self.assertRaises(SystemExit) as sys_exit:
            self.runner.run([op.join(TEST_DIR, "inputs/test_input_pass.py")])
        self.assertEqual(sys_exit.exception.code, 1)
        fnames = [op.join(TEST_DIR, "inputs/test_input_fail.py")]
        with self.assertRaises(SystemExit) as sys_exit:
            self.runner.run(fnames)
        self.assertEqual(len(self.runner.failed_files), 2)

    def test_rcfile(self):
        # rcfile does not exist, handle it
        self.runner.rcfile = '.pylintrc2'
        with self.assertRaises(SystemExit) as sys_exit:
            self.runner.run([op.join(TEST_DIR, "inputs/test_input_pass.py")])
        self.assertEqual(sys_exit.exception.code, 0)
        self.runner.rcfile = op.join(op.abspath(op.join(TEST_DIR, '..')), '.pylintrc')
        with self.assertRaises(SystemExit) as sys_exit:
            self.runner.run([op.join(TEST_DIR, "inputs/test_input_pass.py")])
            self.assertEqual(sys_exit.exception.code, 0)

    def test_crash(self):
        with self.assertRaises(SystemExit) as sys_exit:
            self.runner.run([op.join(TEST_DIR, "inputs/test_input_crash.py")])
            self.assertEqual(sys_exit.exception.code, 1)

    def test_silent_crash(self):
        self.runner.keep_results = True
        with self.assertRaises(SystemExit):
            self.runner.run([op.join(TEST_DIR, "inputs/test_input_pass.py")])
        self.runner.results.linter.stats = {'global_note': False}
        self.assertTrue(self.runner.check_no_silent_crash())
        self.runner.results.linter.stats = {'global_note': False,
                                            'by_msg': {'syntax-error': 1}}
        self.assertFalse(self.runner.check_no_silent_crash())

    def test_parse_args(self):
        """Confirm that inputs are expected type"""
        parsed = parse_args(["-e", "-i", "-t", "9.0", 'test1.py', 'test2.py', 'test3.py'])
        self.assertTrue(len(parsed.fnames), 3)
        self.assertTrue(parsed.ignore_tests)
        self.assertTrue(parsed.allow_errors)
        self.assertEqual(parsed.thresh, 9.0)

    def testCustomRulesSetup(self):
        """Test that setup works correctly"""
        args = Namespace(rcfile=None, thresh=9.0, allow_errors=False,
                         ignore_tests=False, keep_results=False,
                         reduce_logging=False,
                         verbosity=30, custom_path="not_existing")
        with self.assertRaises(Exception):
            PylintRunner(args)
        module_with_slashes = "tests/__init__.py"
        module_without_funcs = "tests"
        # Incorrect path
        args.custom_path = module_with_slashes
        with self.assertRaises(Exception):
            # python2 raises ImportError, python3 ModuleNotFoundError
            PylintRunner(args)
        # No functions in module
        args.custom_path = module_without_funcs
        with self.assertRaises(ValueError):
            PylintRunner(args)

    def test_custom_rules(self):
        """See ../example_customs.py for defined functions"""
        args = Namespace(rcfile=None, thresh=9.0, allow_errors=False,
                         ignore_tests=False, keep_results=False,
                         reduce_logging=False,
                         verbosity=30, custom_path="tests.example_customs")
        self.runner = PylintRunner(args)
        # Functions correctly set
        self.assertTrue(callable(self.runner.custom_rules))
        self.assertTrue(callable(self.runner.custom_score))
        # 1) Pass custom check but do not override (normally fails)
        with self.assertRaises(SystemExit) as sys_exit:
            self.runner.run([op.join(TEST_DIR, "inputs/test_input_crash.py")])
        self.assertEqual(sys_exit.exception.code, 1)
        # 2) Pass custom checks and override (normally fails)
        with self.assertRaises(SystemExit) as sys_exit:
            self.runner.run([op.join(TEST_DIR, "inputs/test_input_fail.py")])
        self.assertEqual(sys_exit.exception.code, 0)
        # 3) Fail custom checks and override (normally passes)
        with self.assertRaises(SystemExit) as sys_exit:
            self.runner.run([op.join(TEST_DIR, "inputs/test_input_pass.py")])
        self.assertEqual(sys_exit.exception.code, 1)


    def tearDown(self):
        self.runner = None

if __name__ == '__main__':
    unittest.main()
