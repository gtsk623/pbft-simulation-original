#-*- coding: utf-8 -*-

from peer import Peer
from globalparam import readfile, known_nodes, timestamp
import sys
import threading

def handlerreply(peerself, msgdata):
    peerself.printdebug("Blockchain finish with packet size = %d" % len(msgdata))
    peerself.endtime = timestamp()
    ss = float((peerself.starttime.split(":"))[2])
    se = float((peerself.endtime.split(":"))[2])
    peerself.printdebug("Blockchain start at %s, finsh at %s" % (peerself.starttime, peerself.endtime))
    peerself.printdebug("T = %f" % round(se - ss, 6))
    
handler_list = {
        "REPLY" : ("REPL", handlerreply)
    }

class System(Peer) : 
    def __init__(self, ip, port, fixed_packet_size):
        Peer.__init__(self, ip, port)
        
        self.peer_id = "System"
        fixed_packet = ""
        for i in range(0, int(fixed_packet_size)):
            fixed_packet += "A"
        self.packet = fixed_packet
        
        self.starttime = 0
        self.endtime = 0
        
        self.count = 0
        
        for handler in handler_list :
            self.addhandler(handler_list[handler][0], handler_list[handler][1])
    
    def requestpropagate(self):
        self.starttime = timestamp()
        self.broadcasttopeers("REQU", self.packet)
            
    def mainloop(self):
        """
        Main loop : To wait received connection from other nodes and to handle received data.
        """
        self.printdebug('System started: %s (%s:%d)' % (self.peer_id, self.server_ip, self.server_port))
        
        s = self.makeserversocket(self.server_port)
        s.settimeout(2)
        
        while True:
            try:
                # scheduling hardcoding
                if self.count < 100 :
                    self.count += 1
                if self.count == 5 :
                    self.printdebug("Blockchain Start")
                    self.requestpropagate()
                # end scheduling
                
                Peer.printdebug(self, 'Listening for connections... %d' % self.count)
                clientsock, clientaddr = s.accept()
                clientsock.settimeout(None)
                
                t = threading.Thread(target=self.handlepeer, args=[ clientsock ])
                t.start()      
            except KeyboardInterrupt:
                self.printdebug('KeyboardInterrupt: stopping mainloop')
                break
            except:
                continue
        # end while loop
        self.printdebug('Mainloop Exiting')
        s.close()
    # end mainloop method
    
if __name__ == '__main__' :
    system = System(sys.argv[1], sys.argv[2], sys.argv[4])
    system.debug = 1
    readfile(sys.argv[3])
    system.peers_list = known_nodes
    del system.peers_list["System"]
    system.mainloop()