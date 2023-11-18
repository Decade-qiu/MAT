
def splitRange(start, end, L):
    res = []
    mask = ((1 << 16)-1) ^ ((1 << L)-1)
    print(bin(mask))
    while 1:
        if start&mask == end&mask:
            res.append((start, end))
            break
        else:
            res.append((start, start|((1<<L)-1)))
            start = start|((1<<L)-1)
            start += 1
    return res

start = 0xBF14
end = 0xBF22
L = 4
print(f"{bin(start)} ~ {bin(end)}")
result = splitRange(start, end, L)
for (subStart, subEnd) in result:
    print(f"{bin(subStart)} ~ {bin(subEnd)}")