pages = []
trial = 20

for _ in range(0, 2*trial):
    input_str = input()
    pages.append(input_str)

i = 0
delays = []
ledgers = []
for p in pages :
    if i % 2 == 0 :
        delays.append(p)
    else :
        ledgers.append(p)
    i += 1    
    
for i in range(0, trial) :
    print(delays[i])

for i in range(0, trial) :
    print(ledgers[i])