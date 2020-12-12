a = [1, 2, 3]
msg = {}
msg['a'] = 1
msg['b'] = 2
print(msg)

msg2 = msg.copy()
msg2['c'] = 3
print(msg)
print(msg2)

if 'c' in msg2.keys() :
    print("hi")