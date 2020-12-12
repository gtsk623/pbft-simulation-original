from datetime import datetime
import sys
import function
import time

""" handler for blockchain messages """
def handlerrequest(peerself, msgdata) :
    peerself.printdebug("Got the request message")
    peerself.state = 'PRE-PREPARE'
    peerself.view += 1
    
    peerself.printdebug("%s, %d" % (peerself.state, peerself.view))
    # peerself.broadcasttopeers("PREP", msgdata)

def handlerpreprepare(peerself, msgdata):
    peerself.printdebug2("Got the pre-prepare message")
    # Peer with status=None can deal with pre-prepare message
    #if peerself.bc.status == None :
    # message check
    if msgdata['status'] == 'PRE-PREPARE' :
        if msgdata['v'] == peerself.bc.view :
            # if function.hash256(msgdata['m']) == msgdata['d(m)'] :
            # 해결해야 할 문제임, json 함수가 dict의 순서를 바꾸어 버리기 때문에 hash 값이 달라지는 현상으로 인해 hash 확인이 되지 않음.
            # 단순 구현 자체에는 문제를 주지 않기 때문에 패스하였음.
            peerself.bc.setpreprepare(msgdata)
            peerself.broadcasttopeers("PREP", peerself.bc.makepreparemsg())
            if peerself.bc.checkprepared() :
                peerself.bc.setprepared()
                peerself.broadcasttopeers("COMM", peerself.bc.makecommitmsg())
    else :
        print(peerself.peerid + " Receives PPRE, but I'm " + peerself.bc.status)

def handlerprepare(peerself, msgdata):
    peerself.printdebug2("Got the prepare message")
    #if peerself.bc.status == 'PRE-PREPARE' or peerself.bc.status == 'PREPARE' :
    if msgdata['status'] == 'PREPARE' :
        if msgdata['v'] == peerself.bc.view :
            peerself.bc.status = 'PREPARE'
            peerself.bc.buffer.append(msgdata) # 미구현
            peerself.bc.countprepare += 1
            if peerself.bc.checkprepared() :
                peerself.bc.setprepared()
                peerself.broadcasttopeers("COMM", peerself.bc.makecommitmsg())
    else :
        # leader will be received more PREP
        print(peerself.peerid + " Receives PREP, but I'm " + peerself.bc.status)
        
def handlercommit(peerself, msgdata):
    peerself.printdebug2("Got the commit message")
    #if peerself.bc.status == 'PREPARE' or peerself.bc.status == 'PREPARED' : # 아직 preprepare가 있을 수 있나?
    if msgdata['status'] == 'COMMIT' :
        if msgdata['v'] == peerself.bc.view :
            peerself.bc.buffer.append(msgdata) # 미구현
            peerself.bc.countcommit += 1
            if peerself.bc.checkcommitted() :
                peerself.bc.setcommitted()
                #print("Consensus is finished with view = " + str(peerself.bc.view))
                #print("Previous hash = " + peerself.bc.prepreparemsg['prev_hash'])
                #print("Number of Blocks = ")
                #print(len(peerself.bc.ledger))
                #print("Ledger in bytes = ")
                #print("Finish")
                delay = time.time() - peerself.bc.prepreparemsg['m']['t']
                data = {}
                data['size'] = peerself.bc.getledgerbytes()
                data['delay'] = delay
                data['peerid'] = peerself.peerid
                #print("> %s view %d finish" % (peerself.peerid, peerself.bc.view))
                peerself.sendtopeer(peerself.bc.leader, "REPL", data)
    else :
        print(peerself.peerid + " Receives COMM, but I'm " + peerself.bc.status)
                    
    #finish
    #peerself.sendtopeer("System", "REPL", msgdata)

def handlerreply(peerself, msgdata): # print and evaluation
    # evaluation
    delay = msgdata['delay']
    size = msgdata['size']
    p = msgdata['peerid']
    #print("%f %f %f" % (size, peerself.peerinfo[p][0], peerself.peerinfo[p][1]))
    if peerself.bc.checkstorageshortage(p, size) :
        #print("%s not enough storage with %d" % (p, size))
        peerself.bc.overpeerid.append(p)
    peerself.bc.totaldelay += delay
    peerself.bc.totalsize += size
    # evaluation
    peerself.bc.countreply += 1
    #print(peerself.bc.countreply)
    if peerself.bc.countreply == len(peerself.bc.peerlist) :
        print(peerself.bc.totaldelay / len(peerself.peerlist))
        print(peerself.bc.totalsize / len(peerself.peerlist))
        nextleader = 'peerid'
        if peerself.bc.overpeerid != [] :
            nextleader = peerself.bc.overpeerid[0]
            #print("nextleader = %s" % nextleader)
        peerself.broadcasttopeers("FINI", nextleader)
        peerself.bc.roundfinish()
        if nextleader != 'peerid' :
            peerself.bc.leader = nextleader
    
def handlerfinish(peerself, msgdata):
    if peerself.bc.prepared and peerself.bc.committed :
        #print("Finish with %s" % peerself.peerid)
        peerself.bc.roundfinish()
        if msgdata != 'peerid' :
            peerself.bc.leader = msgdata
    else :
        return;
        #print("I'm not ready; %s" % peerself.peerid)

class Blockchain():
    def __init__(self, peerid, peerlist, peerinfo):
        # Network
        self.peerid = peerid
        self.peerlist = peerlist
        self.peerinfo = peerinfo
        
        # Blockchain
        self.status = None
        self.view = 0
        self.leader = None
        self.txpool = []
        self.ledger = []
        
        # Processing
        self.requestmsg = None
        self.nrequest = 0
        self.prepreparemsg = None # this msg is block proposal
        self.buffer = [] # 사실 필요 없도록 구현하였음, 원래는 모두 저장해두어 각 인크립션을 확인하여 중복되지 않아야 함. 다만 본 시스템에선 단순히 확인하는 것이기 때문에 드랍함.
        self.countprepare = 0
        self.countcommit = 0
        self.prepared = False
        self.committed = False
        self.countreply = 0
        
        # evaluation
        self.totaldelay = 0
        self.totalsize = 0
        
        # proposed
        self.overpeerid = []
        self.newindex = 0
    
    def roundfinish(self):
        self.status = None
        self.view += 1
        self.leader = None
        
        self.requestmsg = None
        self.nrequest = 0
        self.prepreparemsg = None
        self.buffer = []
        self.countprepare = 0
        self.countcommit = 0
        self.prepared = False
        self.committed = False
        self.countreply = 0
        
        self.totaldelay = 0
        self.totalsize = 0
        
        self.overpeerid = []
        
    def gettimestamp(self):
        dt = datetime.now()
        day = "%s-%s-%s" % (dt.year, dt.month, dt.day)
        time = "%s:%s:%s.%s" % (dt.hour, dt.minute, dt.second, dt.microsecond) 
        return day + " " + time
    
    def leaderelection(self):
        if self.leader == None : 
            index = self.view % len(self.peerlist)
            self.leader = self.peerlist[index]
        return self.leader
    
    def setpreprepare(self, msgdata):
        self.status = 'PRE-PREPARE'
        self.requestmsg = msgdata['m']
        self.nrequest = msgdata['n']
        self.prepreparemsg = msgdata
    
    def setprepared(self):
        self.status = 'PREPARED'
        self.prepared = True
            
    def setcommitted(self):
        self.status = 'COMMITTED'
        self.committed = True
        if 'cp' in self.prepreparemsg.keys():
            if self.checkstorageshortage(self.peerid, self.getledgerbytes()):
                self.ledger = []
                self.newindex = 0
            else :
                self.newindex = len(self.ledger)-1
        self.ledger.append(self.prepreparemsg)
    
    def checkprepared(self):
        if self.prepreparemsg != None and self.checkquorum('PREPARE') and not self.prepared:
            return True
        else :
            return False
        
    def checkcommitted(self):
        if self.prepreparemsg != None and self.prepared and self.checkquorum('COMMIT') and not self.committed:
            return True
        else :
            return False
    
    def checkquorum(self, status):
        n = len(self.peerlist)
        if status == 'PREPARE' :
            if self.countprepare > 0.66*(n-1) :
                return True
            else :
                return False
        elif status == 'COMMIT' :
            if self.countcommit > 0.66*n :
                return True
            else :
                return False
        
    def getledgerbytes(self):
        size = 0
        for lg in self.ledger :
            size += len(function.dicttostr(lg))
        return size
    
    # txpool에서 block을 만들어 내어 request msg를 만들기 위한 함수
    def gettxpool(self):
        transactions = ""
        for tx in self.txpool :
            transactions += function.hash256(str(tx))
        return transactions
    
    def getcompressblock(self):
        txs = ""
        for block in self.ledger[self.newindex:len(self.ledger)] :
            txs += function.hash256(str(block))
        return txs
    
    """ generating blockchain messages """    
    def makerequestmsg(self):
        msg = {}
        msg['status'] = 'REQUEST'
        msg['o'] = self.gettxpool()
        msg['t'] = time.time()
        msg['c'] = self.peerlist[0]
        return msg    
    
    def makecompressmsg(self):
        msg = {}
        msg['status'] = 'REQUEST'
        msg['o'] = self.getcompressblock()
        msg['t'] = time.time()
        msg['c'] = self.peerlist[0]
        return msg
    
    def checkstorageshortage(self, peerid, chainsize):
        if float(chainsize / self.peerinfo[peerid][0]) >= self.peerinfo[peerid][1] :
            return True
        else :
            return False
    
    def makecompressblockmsg(self):
        msg = {}
        if self.ledger == [] :
            # genesis block
            ghash = ""
            for _ in range(0, 64) :
                ghash += "0"
            msg['prev_hash'] = ghash 
        else :
            msg['prev_hash'] = self.ledger[len(self.ledger)-1]['d(m)']
        msg['status'] = 'PRE-PREPARE'
        msg['v'] = self.view
        msg['n'] = self.nrequest
        # request msg digest
        m = self.makecompressmsg()
        msg['d(m)'] = function.hash256(m) # dict to string?
        msg['m'] = m
        return msg
        
    def makeprepreparemsg(self, requestmsg): # block
        msg = {}
        if self.ledger == [] :
            # genesis block
            ghash = ""
            for _ in range(0, 64) :
                ghash += "0"
            msg['prev_hash'] = ghash 
        else :
            msg['prev_hash'] = self.ledger[len(self.ledger)-1]['d(m)']
        msg['status'] = 'PRE-PREPARE'
        msg['v'] = self.view
        if requestmsg == self.requestmsg :
            self.nrequest += 1
        msg['n'] = self.nrequest
        # request msg digest
        msg['d(m)'] = function.hash256(requestmsg) # dict to string?
        msg['m'] = requestmsg
        # new field needs
        if self.checkstorageshortage(self.peerid, self.getledgerbytes()) :
            msg['cp'] = self.makecompressblockmsg()
        return msg
    
    def makepreparemsg(self):
        msg = {}
        msg['status'] = 'PREPARE'
        msg['v'] = self.view
        msg['n'] = self.nrequest
        msg['d(m)'] = self.prepreparemsg['d(m)']
        return msg
        
    def makecommitmsg(self):
        msg = {}
        msg['status'] = 'COMMIT'
        msg['v'] = self.view
        msg['n'] = self.nrequest
        msg['d(m)'] = self.prepreparemsg['d(m)']
        msg['i'] = self.peerid
        return msg
        