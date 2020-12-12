#-*- coding: utf-8 -*-
import json
import hashlib
import normal

#file write
def filecreate(msg):
    f = open("")

# setup nodes for test
def setupnodes(ip, start_port, end_port):
    known_nodes = []
    while start_port <= end_port :
        peerid = "%s:%d" % (ip, start_port)
        if peerid not in known_nodes :
            known_nodes.append(peerid)
        start_port += 1
    return known_nodes

def setupsizeandthreshold(ip, start_port, end_port):
    sat = {}
    num = end_port - start_port + 1
    s = None
    t = None
    if num == 4 :
        s = normal.node4s
        t = normal.node4t
    elif num == 8 :
        s = normal.node8s
        t = normal.node8t
    elif num == 12 :
        s = normal.node12s
        t = normal.node12t
    elif num == 16 :
        s = normal.node16s
        t = normal.node16t
    elif num == 20 :
        s = normal.node20s
        t = normal.node20t
        
    while start_port <= end_port :
        peerid = "%s:%d" % (ip, start_port)
        sat[peerid] = (s[end_port-start_port], t[end_port-start_port])
        start_port += 1
    return sat

def hash256(data):
    t = type(data)
    if t is dict :
        return hashlib.sha256(strtobin(dicttostr(data))).hexdigest()
    elif t is str :
        return hashlib.sha256(strtobin(data)).hexdigest()

def encode(data):
    t = type(data)
    if t is dict :
        return strtobin(dicttostr(data))
    elif t is str :
        return strtobin(data)

def decode(data):
    data = bintostr(data)
    if '{' in data and '}' in data :
        return strtodict(data)
    else :
        return data

"""
HELP FUNCTIONS
"""
def dicttostr(dictionary):
    return json.dumps(dictionary)
def strtobin(string):
    return string.encode()
def bintostr(binary):
    return binary.decode()
def strtodict(string):
    return json.loads(string)
