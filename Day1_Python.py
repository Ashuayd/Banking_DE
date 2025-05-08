from collections import Counter

def first_non_repeating_char(s):
    count = Counter(s)
    for ch in s:
        if count[ch] == 1:
            return ch
        return None
    

s = input("Enter a string: ")
result = first_non_repeating_char(s)
print("First non-repeating character: ", result)
