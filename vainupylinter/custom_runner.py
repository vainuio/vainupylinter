"""
Wrap pylint inside custom class to do some customised handling of the result"
"""
# pylint: disable=line-too-long
from __future__ import absolute_import, print_function
import sys
import argparse
import logging
import importlib
import os.path as op
import pylint
from pylint.lint import Run

try:
    ModuleNotFoundError
except NameError:
    ModuleNotFoundError = ImportError   # pylint: disable=redefined-builtin

try:
    from vainupylinter.print_logger import PrintLogger, redirect_stdout
except ModuleNotFoundError:
    from print_logger import PrintLogger, redirect_stdout

sys.path.append(op.abspath("."))

def parse_args(args):
    """Handle inputs"""
    parser = argparse.ArgumentParser()
    parser.description = 'File specific pylint analysis.'
    parser.add_argument(
        nargs='*',
        type=str,
        dest='fnames',
        help='The files to pylint. Pylinting is performed only to *.py files.'
    )
    parser.add_argument(
        '-r', '--rcfile',
        type=str,
        default='',
        metavar='rcfile',
        help='The path to .pylintrc file with the correct configuration.'
        )
    parser.add_argument(
        '-t', '--thresh',
        type=float,
        default=9.2,
        metavar='thresh',
        help='Threshold the code must reach to pass. Defaults to 9.8.'
    )
    parser.add_argument(
        '-e', '--allow-errors',
        dest='allow_errors',
        default=False,
        action='store_true',
        help="Allow pylint errors"
    )
    parser.add_argument(
        '-i', '--ignore-tests',
        dest='ignore_tests',
        default=False,
        action='store_true',
        help='Allow test files to pass no matter what'
    )
    parser.add_argument(
        '-k', '--keep-results',
        dest='keep_results',
        default=False,
        action='store_true',
        help="Don't erase results when same runner is called multiple times"
    )
    parser.add_argument(
        '-cp', '--custom-path',
        type=str,
        dest='custom_path',
        default="",
        help="Module (path) containing defined custom rules and scoring functions"
    )
    parser.add_argument(
        '-v', '--verbosity',
        type=int,
        dest='verbosity',
        default=20,
        help="Logger verbosity. Defaults to 20 (INFO)"
    )
    return parser.parse_args(args)



class PylintRunner(object):
    """Class wrapper for pylint runner

    Input
    ------
    fnames : list
        Files to pylint.
    rcfile : str | "" (Default)
        Specify location of .pylintrc wanted.
    thresh : float | 9.2 (Default)
        Threshold limit
    allow_errors: bool | False (Default)
        If True, return zero exit-code when pylint emits error message.
        Default behaviour is to return exit code 1.
    ignore_tests : bool | False (Default)
        If True, test files will always pass
    keep_results : bool | False (Default)
        Save .coverage result to allow score comparisons
    custom-path: str | ""
        Module path to a file that contains custom_rules and custom_scoring.
        These have to defined as follows:
        custom_rules: function
            Input: self.result.linter.stats (dict), filepath as str
            Output: tuple[bool, bool] (passed, override)
        custom_score: function
            Input: self.result.linter.stats (dict)
                Contains the stats outputted by pylint runner
            Output: custom_score, override pylint : tuple(bool, bool)
        custom_thresholding: function
            Input: score (float), threshold (float), filepath as str
            Output: bool

    """
    def __init__(self, args):
        self.rcfile = args.rcfile if args.rcfile else None
        self.thresh = args.thresh
        self.allow_errors = args.allow_errors
        self.ignore_tests = args.ignore_tests
        self.keep_results = args.keep_results
        self.failed_files = []
        self.custom_failed = []
        self.results = None
        self.fname = None
        self.logging = logging
        self.logging.basicConfig(level=args.verbosity,
                                 format='%(message)s')
        custom_rules, custom_score, custom_thresholding = self.set_custom_functions(args.custom_path)
        self.custom_rules = custom_rules
        self.custom_score = custom_score
        self.custom_thresholding = custom_thresholding

    def set_custom_functions(self, custom_path):
        """Use input module to import custom rules and custom scoring function"""
        if not custom_path:
            return None, None, None
        custom_module = importlib.import_module(custom_path)
        try:
            custom_rules = getattr(custom_module, "custom_rules")
        except AttributeError:
            self.logging.warning("No 'custom_rules' defined in {}".format(custom_path))
            custom_rules = None
        try:
            custom_score = getattr(custom_module, "custom_score")
        except AttributeError:
            self.logging.warning("No 'custom_score' defined in {}".format(custom_path))
            custom_score = None
        try:
            custom_thresholding = getattr(custom_module, "custom_thresholding")
        except AttributeError:
            self.logging.warning("No 'custom_score' defined in {}".format(custom_path))
            custom_thresholding = None
        if not custom_rules and not custom_score and not custom_thresholding:
            raise ValueError("Custom module given but no custom_rules, custom_score found OR custom_thresholding!")
        return custom_rules, custom_score, custom_thresholding


    def clean_up(self):
        """Clean results if same instance is going to be used"""
        self.fname = None
        self.failed_files = []
        self.custom_failed = []
        self.results = None

    def run_pylint(self, fname):
        """Run pylint for specified file"""
        if '.py' not in fname:
            return False
        if not op.isfile(fname):
            self.logging.info('------------------------------------------------------------------')
            self.logging.info("FILE {} DOES NOT EXIST.".format(fname))
            self.logging.info('------------------------------------------------------------------')
            self.logging.info('\n')
            return False
        self.logging.info("{}\n".format(fname))
        self.fname = fname
        if self.rcfile and op.isfile(self.rcfile):
            command_arg = [fname, '--rcfile', self.rcfile, '--score', 'no']
        else:
            command_arg = [fname, '--score', 'no']
        try:
            with redirect_stdout(PrintLogger(name="pylint", log_level="INFO")):
                if int(pylint.__version__[0]) < 2:
                    self.results = Run(command_arg, exit=False) # pylint: disable=unexpected-keyword-arg
                else:
                    # Use the default one
                    self.results = Run(command_arg, do_exit=False)   # pylint: disable=unexpected-keyword-arg
                return True
        except Exception as error:  # pylint: disable=broad-except
            # We want to crash if ANYTHING goes wrong
            self.logging.warning('------------------------------------------------------------------')
            self.logging.warning("PYLINT CRASHED WHILE HANDLING {}".format(fname))
            self.logging.warning("{}: {}".format(type(error), error.args))
            self.logging.warning('------------------------------------------------------------------')
            self.logging.info('\n')
            self.failed_files.append(fname)
            return False

    def check_no_silent_crash(self, override=False):
        """Syntax error may cause pylint to fail without an actual exception. Or the file may
        just be defined to be ignored in .pylintrc"""
        if self.results:
            score = self.results.linter.stats.get('global_note', False)
            if score is False:
                messages = self.results.linter.stats.get('by_msg', {})
                if messages.get('syntax-error', False) and not override:
                    self.logging.warning('\n------------------------------------------------------------------')
                    self.logging.warning('PYLINT FAILED BECAUSE SYNTAX ERROR.')
                    self.logging.warning('------------------------------------------------------------------')
                    self.logging.warning('\n')
                    self.failed_files.append(self.fname)
                    return False
                self.logging.info('\n------------------------------------------------------------------')
                self.logging.info('FILE WAS IGNORED.')
                self.logging.info('------------------------------------------------------------------')
            return True
        return False

    def check_custom_rules(self):
        """Check if custom rules passed"""
        if self.custom_rules:
            with redirect_stdout(PrintLogger(name="pylint", log_level="INFO")):
                passed_custom, override = self.custom_rules(self.results.linter.stats, self.fname)
            if not passed_custom:
                self.logging.warning("{} FAILED CUSTOM CHECKS".format(self.fname))
                self.custom_failed.append(self.fname)
            return passed_custom, override
        return False, False

    def check_score(self):
        """Return standard score or customised score"""
        if self.custom_score:
            with redirect_stdout(PrintLogger(name="pylint", log_level="INFO")):
                return self.custom_score(self.results.linter.stats)
        return self.results.linter.stats.get('global_note', False)

    def check_threshold(self, score):
        """Check if custom / standard threshold limit is accepted"""
        if self.custom_thresholding:
            with redirect_stdout(PrintLogger(name="pylint", log_level="WARNING")):
                return self.custom_thresholding(score, self.thresh, self.fname)
        elif score < self.thresh:
            self.logging.warning("SCORE {} IS BELOW THE THRESHOLD {} for {}".format(score, self.thresh,
                                                                                    self.fname))
            return False
        return True

    def eval_results(self, passed_custom, override):
        """Do some custom checking based on the results"""
        errors = self.results.linter.stats.get('error', False)
        fatal = self.results.linter.stats.get('fatal', False)
        score = self.check_score()
        file_passed = True
        self.logging.info('\n------------------------------------------------------------------\n')
        self.logging.info('Your code has been rated at {0:.2f}/10\n'.format(score))
        self.logging.info('\n')
        self.logging.info('------------------------------------------------------------------')
        if fatal:
            self.logging.warning("FATAL ERROR(S) DETECTED IN {}.".format(self.fname))
            file_passed = False
        if errors and not self.allow_errors:
            self.logging.warning("ERROR(S) DETECTED IN {}.".format(self.fname))
            file_passed = False
        if score:
            file_passed = file_passed and self.check_threshold(score)
        if self.custom_rules and passed_custom != file_passed and override:
            self.logging.info("OVERRIDING STANDARD RESULT WITH CUSTOM FROM {} TO {}.".format(file_passed,
                                                                                             passed_custom))
            file_passed = passed_custom
        if not file_passed and self.ignore_tests and ("test_" in self.fname.split("/")[-1] or \
                                                      "tests.py" in self.fname):
            self.logging.info("ASSUMING {} IS TEST FILE. ALLOWING.".format(self.fname))
            self.logging.info('------------------------------------------------------------------\n')
        elif file_passed:
            self.logging.info('FILE {} PASSED PYLINT, THRESHOLD {}'.format(self.fname, self.thresh))
        else:
            self.failed_files.append(self.fname)
        self.logging.warning('------------------------------------------------------------------')

    def report_results(self):
        """Final summary report"""
        if not self.failed_files and not self.custom_failed:
            self.logging.info('------------------------------------------------------------------')
            self.logging.info("PYLINT WAS SUCCESSFUL!")
            self.logging.info('------------------------------------------------------------------')
            return 0
        self.logging.warning('------------------------------------------------------------------')
        self.logging.warning("PYLINTING FAILED")
        if self.failed_files:
            self.logging.warning('------------------------------------------------------------------')
            self.logging.warning("THE FOLLOWING FILES DID NOT PASS.")
            self.logging.warning('\n'.join(self.failed_files))
            self.logging.info('------------------------------------------------------------------')
        if self.custom_failed:
            self.logging.warning('------------------------------------------------------------------')
            self.logging.warning("THE FOLLOWING FILES FAILED CUSTOM CHECKS.")
            self.logging.warning('\n'.join(self.custom_failed))
            self.logging.info('------------------------------------------------------------------')
        return 1
# pylint: enable=line-too-long
    def run(self, fnames):
        """Run for specified files. Lint each file indepedently
        Input
        -----
        fnames : list
            List of filenames to lint.
        """
        logging.info("Starting")
        for fname in fnames:
            linted = self.run_pylint(fname=fname)
            if linted:
                custom_ok, override_standard = self.check_custom_rules()
                override = custom_ok and override_standard
                success = self.check_no_silent_crash(override=override)
                if success:
                    self.eval_results(custom_ok, override)
        exit_code = self.report_results()
        if not self.keep_results:
            self.clean_up()
        sys.exit(exit_code)


def run():
    """Start the custom pylint run"""
    args = parse_args(sys.argv[1:])
    fnames = args.fnames
    runner = PylintRunner(args)
    runner.run(fnames)


if __name__ == '__main__':
    run()
