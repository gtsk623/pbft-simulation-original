#-*- coding: utf-8 -*-

from peer import Peer
import function
import multiprocessing
import blockchain

handler_list = {
        "REQUEST" : ("REQU", blockchain.handlerrequest),
        "PRE-PREPARE" : ("PPRE", blockchain.handlerpreprepare),
        "PREPARE" : ("PREP", blockchain.handlerprepare),
        "COMMIT" : ("COMM", blockchain.handlercommit),
        "REPLY" : ("REPL", blockchain.handlerreply),
        "FINISH" : ("FINI", blockchain.handlerfinish)
    }

def generatepeer(ip, port, known_nodes, peerinfo):
    """ To generate a peer with a port number. """
    peer = Peer(ip, port)
    peer.debug = 0
    peer.debug2 = 0
    # handler setup
    for handler in handler_list :
        peer.addhandler(handler_list[handler][0], handler_list[handler][1])
    # peer list setup
    for node in known_nodes :
        peer.peerlist.append(node)
    # blockchain ready
    peer.peerinfo = peerinfo
    peer.setupblockchain()
    # peer start
    peer.mainloop()

""" Main method """
if __name__ == '__main__' :
    start_port = 8000
    end_port = 8007
    known_nodes = function.setupnodes("127.0.0.1", start_port, end_port)
    sat = function.setupsizeandthreshold("127.0.0.1", start_port, end_port)
    for node in known_nodes :
        p = multiprocessing.Process(target=generatepeer, args=(node.split(":")[0], node.split(":")[1], known_nodes, sat))
        p.start()
    