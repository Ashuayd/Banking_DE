text = input()

words = text.split() 
freq = {}         

for i in words:
    if i in freq:
        freq[i] += 1
    else:
        freq[i] = 1

print(freq)

sorted_words = sorted(freq.items(), key=lambda item: item[1], reverse=True)

print()
for word, count in sorted_words[:10]:
    print(f"{word} : {count}")
