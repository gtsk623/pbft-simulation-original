#-*- coding: utf-8 -*-
import function
import socket
import struct
import threading
import traceback
import blockchain

class Peer:    
    def __init__(self, ip, port):
        self.debug = 0
        self.debug2 = 0
        self.server_ip = ip
        self.server_port = int(port)
        self.peerid = "%s:%d" % (self.server_ip, self.server_port)
        self.peerlist = []    
        self.handlers = {}
        self.bc = None
        self.peerinfo = {}
        
        self.delay = None
    
    def setupblockchain(self):
        self.bc = blockchain.Blockchain(self.peerid, self.peerlist, self.peerinfo)
    
    def printdebug(self, msg):
        if self.debug :
            print("[%s] (%s) %s" % (self.peerid, self.bc.gettimestamp(), msg))
    
    def printdebug2(self, msg):
        if self.debug2 :
            print("%s %s" % (self.peerid, msg))
    
    def addhandler(self, msgtype, handler):
        """ Registers the handler for the given message type with this peer """
        assert len(msgtype) == 4
        self.handlers[msgtype] = handler
    
    def addpeer(self, ip, port):
        peerid = "%s:%d" % (ip, port)
        if peerid not in self.peerlist.keys() :
            self.peerlist[peerid] = (ip, port)
    
    def makeserversocket(self, port, backlog=5):
        """ To construct and prepare a server socket listening on the given port. """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', port))
        s.listen(backlog)
        return s
    
    def handlepeer(self, clientsock):
        """ To handle peer when receiving. """
        self.printdebug('New child %s' % str(threading.currentThread().getName()))
        self.printdebug('Incoming connection from %s' % str(clientsock.getpeername()))
    
        host, port = clientsock.getpeername()
        peer_conn = PeerConnection(host, port, clientsock)
        
        try:
            msgtype, msgdata = peer_conn.recvdata()
            msgtype = msgtype.decode()
            msgdata = function.decode(msgdata)
            
            if msgtype: 
                msgtype = msgtype.upper()
            if msgtype not in self.handlers:
                self.printdebug('Cannot handled: %s: %s' % (msgtype, msgdata))
            else:
                #t = threading.Thread(target=self.handlers[ msgtype ], args=(self, msgdata))
                #t.start()
                self.handlers[ msgtype ](self, msgdata)
        except KeyboardInterrupt:
            raise
        except:
            if self.debug:
                traceback.print_exc()
        
        self.printdebug('Disconnecting ' + str(clientsock.getpeername()))
        peer_conn.close()
    # end handlepeer method
    
    def broadcasttopeers(self, msgtype, msgdata):
        for peerid in self.peerlist :
            if peerid != self.peerid :
                self.sendtopeer(peerid, msgtype, msgdata)
    
    def sendtopeer(self, destination_peerid, msgtype, msgdata):
        # destination peer id = ip:port
        destination_ip = destination_peerid.split(":")[0]
        destination_port = destination_peerid.split(":")[1]
        # try to send
        try :
            pc = PeerConnection(destination_ip, destination_port)
            pc.senddata(msgtype, msgdata)
            
            #self.printdebug2("Send to %s:%d (type=%s)" % (destination_ip, int(destination_port), msgtype))
            self.printdebug2(" --%s--> %s:%d" % (msgtype, destination_ip, int(destination_port)))
        except KeyboardInterrupt:
            raise
        except:
            if self.debug:
                traceback.print_exc()
    
    def proposeblock(self):
        #print("%s is leader!!!" % self.peerid)
        #print("----------Start (view %d) ----------" % self.bc.view)
        msgtosend = self.bc.makeprepreparemsg(self.bc.makerequestmsg())
        self.bc.setpreprepare(msgtosend)
        self.broadcasttopeers('PPRE', msgtosend)
        
    def mainloop(self):
        self.printdebug('Server started: %s (%s:%d)' % (self.peerid, self.server_ip, self.server_port))
        s = self.makeserversocket(self.server_port)
        s.settimeout(2)
        # instead of transaction request
        for i in range(0, 250) :
            self.bc.txpool.append(i)
        while True :
            try:
                if self.bc.status == None and self.bc.leaderelection() == self.peerid :
                    threading.Timer(1, self.proposeblock).start()
                    self.bc.status = 'PRE-PREPARE' # escape check of leader status
                else :
                    self.printdebug('Listening for connections...')
                    clientsock = s.accept()[0]
                    clientsock.settimeout(None)
                    t = threading.Thread(target=self.handlepeer, args=[ clientsock ])
                    t.start()
            except KeyboardInterrupt:
                self.printdebug('KeyboardInterrupt: stopping mainloop')
                break
            except:
                continue
                # if self.debug:
                #    traceback.print_exc()
                #    continue 
        # end while loop
        self.printdebug('Mainloop Exiting')
        s.close()
    # end mainloop method
    
# end BTPeer class

class PeerConnection:
    def __init__(self, destination_ip, destination_port, sock=None):
        if not sock:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((destination_ip, int(destination_port)))
        else:
            self.s = sock
        # open socket file (make)
        self.sd = self.s.makefile("brw", 0)

    def __makemsg(self, msgtype, msgdata):
        # to binary
        msgtype = msgtype.encode()
        msgdata = function.encode(msgdata)
        msglen = len(msgdata)
        msg = struct.pack("!4sL%ds" % msglen, msgtype, msglen, msgdata) 
        return msg

    def senddata(self, msgtype, msgdata):
        try:
            msg = self.__makemsg(msgtype, msgdata)
            self.sd.write(msg)
            self.sd.flush()
        except KeyboardInterrupt:
            raise
        except:
            if self.debug:
                traceback.print_exc()
            return False
        return True

    def recvdata(self):
        try:
            msgtype = self.sd.read(4)
            if not msgtype :
                return (None, None)
            lenstr = self.sd.read(4)
            msglen = int(struct.unpack("!L", lenstr)[0])
            msg = b''
            while len(msg) != msglen :
                data = self.sd.read(min(2048, msglen - len(msg)))
                if not len(data) :
                    break
                msg += data
            if len(msg) != msglen :
                return (None, None)
        except KeyboardInterrupt :
            raise
        except :
            if self.debug :
                traceback.print_exc()
            return (None, None)
        return (msgtype, msg)
    # end recvdata method

    def close(self):
        self.s.close()
        self.s = None
        self.sd = None
