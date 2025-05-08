# In the given list of n ,find the missing numbers

n = [1,4,6,8,3,6,8,9,3,2,6,8,4]

n = sorted(set(n))
lst = []

def missing():
    for i in range(n[0],len(n) + 1):
        if i not in n:
            lst.append(i)
    return lst

print(missing())
        

def missing2():
    for i in n:
        if i not in n:
            lst.append(i)
    return lst

print(missing2())

def missing3():
    return [i for i in range(n[0], n[-1] + 1) if i not in n]

print(missing3())

def missing_with_set_difference():
    full_set = set(range(n[0], n[-1] + 1))  # Set of all numbers in the range
    return list(full_set - set(n))  # Return the missing numbers

print(missing_with_set_difference())

        