from twisted.internet import task, reactor

from p2pserver import P2PServer
from taskserver import TaskServer

from taskbase import TaskHeader
from exampletasks import VRayTracingTask

from hostaddress import getHostAddress

from managerserver import ManagerServer
from nodestatesnapshot import NodeStateSnapshot
from message import MessagePeerStatus

import sys
import time
import random
import socket

class Client:

    ############################
    def __init__(self, configDesc ):

        self.configDesc     = configDesc

        self.lastPingTime   = 0.0
        self.p2pserver      = None
        self.taskServer     = None 
        self.lastPingTime   = time.time()
        self.lastNSSTime    = time.time()

        self.lastNodeStateSnapshot = None

        self.hostAddress    = getHostAddress()

        self.doWorkTask     = task.LoopingCall(self.__doWork)
        self.doWorkTask.start(0.1, False)
       
    ############################
    def startNetwork(self ):
        print "Starting network ..."
        self.p2pserver = P2PServer( self.hostAddress, self.configDesc )

        time.sleep( 1.0 )

        self.taskServer = TaskServer( self.hostAddress, self.configDesc )
        #if self.configDesc.addTasks:
        #    hash = random.getrandbits(128)
        #    th = TaskHeader( str( hash ), "10.30.10.203", self.taskServer.curPort )
        #    t = VRayTracingTask( 100, 100, 10, th )
        #    self.taskServer.taskManager.addNewTask( t )

        self.p2pserver.setTaskServer( self.taskServer )

    ############################
    def stopNetwork(self):
        #FIXME: Pewnie cos tu trzeba jeszcze dodac. Zamykanie serwera i wysylanie DisconnectPackege
        self.p2pserver = None
        self.taskServer = None

    ############################
    def __doWork(self):
        if self.p2pserver:
            if self.configDesc.sendPings:
                self.p2pserver.pingPeers( self.pingsInterval )

            self.p2pserver.syncNetwork()
            self.taskServer.syncNetwork()

            if time.time() - self.lastNSSTime > self.configDesc.nodeSnapshotInterval:
                self.__makeNodeStateSnapshot()
                self.lastNSSTime = time.time()

                #self.managerServer.sendStateMessage( self.lastNodeStateSnapshot )

    ############################
    def __makeNodeStateSnapshot( self, isRunning = True ):

        peersNum            = len( self.p2pserver.peers )
        lastNetworkMessages = self.p2pserver.getLastMessages()

        if self.taskServer:
            tasksNum                = len( self.taskServer.taskHeaders )
            remoteTasksProgresses   = self.taskServer.taskComputer.getProgresses()
            localTasksProgresses    = self.taskServer.taskManager.getProgresses()
            lastTaskMessages        = self.taskServer.getLastMessages()
            self.lastNodeStateSnapshot = NodeStateSnapshot(     isRunning
                                                           ,    self.configDesc.clientUuid
                                                           ,    peersNum
                                                           ,    tasksNum
                                                           ,    self.p2pserver.hostAddress
                                                           ,    self.p2pserver.curPort
                                                           ,    lastNetworkMessages
                                                           ,    lastTaskMessages
                                                           ,    remoteTasksProgresses  
                                                           ,    localTasksProgresses )
        else:
            self.lastNodeStateSnapshot = NodeStateSnapshot( self.configDesc.clientUuid, peersNum )

        if self.p2pserver:
            self.p2pserver.sendClientStateSnapshot( self.lastNodeStateSnapshot )
