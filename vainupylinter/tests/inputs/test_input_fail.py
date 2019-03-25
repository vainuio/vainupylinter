# This is test file to be linted

def custom_summer(a = 1, b = 2):    # Cause some whitespace
    return a + b

def custom_summer_two(a=1, b='2'):
    return a + b

def do_list_things(list_thing):
    if len(list_thing) > 0: # complaints
        return list_thing[1]
    else:
        return None

def main():
    sum1 = custom_summer()
    sum2 = custom_summer_two()
    list_result = do_list_things([1, 2, 3])
    if list_result != None:
        print(sum1 == sum2)
        print(k)

if __name__ == "__main__":
    main()
