# Vainu pylinter

The purpose of this module is to allow easy import to the vainu repositories using python.

The repository contains
* custom_runner.py : Lints each file separately. If any of the files fail, the runner will return exit code 1.
* vainupylinter : console script

Current implementation is python2 and python3 compatible. This can change in the future.

## Installation

Install the module with pip:

`pip install git+https://github.com/vainuio/vainupylinter.git`


Add the module to requirements.txt using "git+https://github.com/vainuio/vainupylinter.git".

### Requirements
pylint

And that's it!

## How to use

To check files with custom pylinter, use

`vainupylinter <FNAME1> <FNAME2> ...`

## DEVELOPING

Make sure that you have enabled commit hooks in .githooks:

`vainupylinter <FNAME1> <FNAME2> ...`



## Inputs

| Argument            | Type  | Default | Required | Description                                                             |
|---------------------|-------|---------|----------|-------------------------------------------------------------------------|
|                     | str   |         | Yes      | File paths to be checked. Separated by space                            |
| --thresh, -t        | float | 9.2     | No       | Threshold for files to be considered OK                                 |
| --rcfile, -r        | str   | ""      | No       | Custom path for .pylintrc file. If not given, defaults to pylint logic. |
| --allow-errors, -e  | bool  | False   | No       | Return zero exit-code even though pylint emits an error-level message   |
| --keep-results, -r  | bool  | False   | No       | Do not clean up runner in between runs.                                 |
| --custom_path, -cp  | str   | ""      | No       | Use custom rules and scoring. See Custom settings below.                |

## Custom settings

Vainupylinter supports following features:

1) Custom rules:
    - Allows users to define their own logic whether file should be accepted. For example, one can implement logic that does not allow pdb.set_trace() to be used
    - The function MUST BE named `custom_rules`. Input is expected to be a 1) stats from linter result and file path and output has to be tuple containing 2 floats: did the file pass and should the result override the standard check.
2) Custom scoring:
    - Allows users to define custom scoring function. For example, if one wants to treat certain type of warning as fatal message.
    - The function MUST BE named `custom_score`. `stats` containing the pylint result statistics is given as input and output is expected to be boolean
3) Custom thresholding
    - Allows more complex threshold checks. For example, files in specified subdirectories can have different threshold than in main.
    - The function MUST BE named `custom_thresholding`. The function takes  score, default threshold and fname as input, and returns bool (passed or not)

These functions should be defined in the same python file. The `--custom_path` argument needs to be module path (so rules.custom_rules instead of rules/custom_rules.py). You may have to add  `__init__.py` for the import to work. The file must be in the directory or subdirectory of the directory vainupylinter is called.

In the following file structure, vainupylinter can find rules from `project`, `folder1` and `subfolder1` when called at project-level. If vainupylinter is called in `subfolder1`, rules cannot be found from `folder1`or its parent directory.

```
project
│   README.md
│   __init__.py  
│
└───folder1
│   │   __init__.py
│   │  code1.py
│   │
│   └───subfolder1
│       │   __init__.py
│       │   
│       │   ...
│   
└───folder2
    │   code2.py

```


Remember, that if you want the option to silence the defined custom warnings, you have to add logic for it in `custom_rules` function.
