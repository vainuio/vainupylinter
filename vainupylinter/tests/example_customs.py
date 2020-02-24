"""Examples to test that custom rules and scoring work as expected"""
from __future__ import print_function

def custom_rules(stats, fname=None):
    """For testing custom rules: do not allow any prints
    INPUTS:
        fname: (str)
            path to a file that is checked
    OUTPUT:
        tuple[accepted, override]: bool
            accepted : whether the file passed or not
            override : over standard check result
    """
    if "test_input_crash.py" in fname:
        return True, False
    if "test_input_fail.py" in fname:
        return True, True

    return False, True

def custom_score(stats):
    """Treats wildcards as errors"""
    convention = stats['convention']
    error = stats['error']
    refactor = stats['refactor']
    warning = stats['warning']
    statement = stats['statement']
    wildcards = stats['by_msg'].get('wildcard-import', False)
    if wildcards:
        warning = warning - wildcards
        error = error + wildcards
        return 10.0 - ((float(5 * error + warning + refactor + convention) / statement) * 10)
    return stats['global_note']
