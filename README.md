# Vainu pylinter

The purpose of this module is to allow easy import to the vainu repostories using python.

The repository contains
* custom_runner.py : Lints each file separately. If any of the files fail, the runner will return exit code 1.
* vainupylinter : console script

## Installation

Install the module with pip:

`pip install git+https://github.com/vainuio/vainupylinter.git`


Add the module to requirements.txt using "git+https://github.com/vainuio/vainupylinter.git".

### Requirements
pylint


## How to use

To check files with custom pylinter, use

`vainupylinter <FNAME1> <FNAME2> ...`
