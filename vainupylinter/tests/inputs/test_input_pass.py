"""This is test file to be linted"""
from __future__ import print_function

def custom_summer(val1=1, val2=2):    # Cause some whitespace
    """Maths!"""
    return val1 + val2

def custom_summer_two(val1=1, val2='2'):
    """Different defaults!"""
    return val1 + val2

def do_list_things(list_thing):
    """Get first item in list"""
    if list_thing: # complaints
        return list_thing[0]
    return None

def main():
    """Do all the things!"""
    sum1 = custom_summer()
    sum2 = custom_summer_two()
    list_result = do_list_things([1, 2, 3])
    if list_result:
        print(sum1 == sum2)

if __name__ == "__main__":
    main()
