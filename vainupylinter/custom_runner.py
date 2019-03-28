"""
Wrap pylint inside custom class to do some customised handling of the result"
"""
# pylint: disable=line-too-long
from __future__ import print_function
import sys
import logging
import argparse
import os.path as op
import pylint
from pylint.lint import Run


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
        type=int,
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
    """
    def __init__(self, args):
        self.rcfile = args.rcfile if args.rcfile else None
        self.thresh = args.thresh
        self.allow_errors = args.allow_errors
        self.ignore_tests = args.ignore_tests
        self.keep_results = args.keep_results
        self.failed_files = []
        self.results = None
        self.fname = None
        self.logging = logging
        self.logging.basicConfig(level=args.verbosity,
                                 format='%(message)s')

    def clean_up(self):
        """Clean results if same instance is going to be used"""
        self.fname = None
        self.failed_files = None
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

    def check_no_silent_crash(self):
        """Syntax error may cause pylint to fail without an actual exception. Or the file may
        just be defined to be ignored in .pylintrc"""
        if self.results:
            score = self.results.linter.stats.get('global_note', False)
            if score is False:
                messages = self.results.linter.stats.get('by_msg', {})
                if messages.get('syntax-error', False):
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

    def eval_results(self):
        """Do some custom checking based on the results"""
        errors = self.results.linter.stats.get('error', False)
        fatal = self.results.linter.stats.get('fatal', False)
        score = self.results.linter.stats.get('global_note', False)
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
        if score and score < self.thresh:
            self.logging.warning("SCORE {} IS BELOW THE THRESHOLD {} for {}".format(score, self.thresh,
                                                                                    self.fname))
            file_passed = False
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
        if not self.failed_files:
            self.logging.info('------------------------------------------------------------------')
            self.logging.info("PYLINT WAS SUCCESSFUL!")
            self.logging.info('------------------------------------------------------------------')
            return 0
        else:
            self.logging.warning('------------------------------------------------------------------')
            self.logging.warning("PYLINTING FAILED. THE FOLLOWING FILES DID NOT PASS.")
            self.logging.warning('\n'.join(self.failed_files))
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
                success = self.check_no_silent_crash()
                if success:
                    self.eval_results()
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
