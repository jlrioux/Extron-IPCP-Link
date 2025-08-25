'''
from extronlib.engine import IpcpLink
link = IpcpLink('172.16.1.10','AVLAN')


from extronlib.interface import EthernetServerInterfaceEx
from extronlib.system import Wait
serv = EthernetServerInterfaceEx(1111)

serv.StartListen()

def handleconnect(client,state):
    print('Connect:{} {}'.format(client.IPAddress,state))

def handledisconnect(client,state):
    print('Disconnect:{} {}'.format(client.IPAddress,state))

def handlerecv(client,data):
    print('RecieveData:{} {}'.format(client.IPAddress,data.decode()))

    @Wait(1)
    def w():
        client.Send('pong:{}'.format(data.decode()))

serv.Connected = handleconnect
serv.Disconnected = handledisconnect
serv.ReceiveData = handlerecv

'''










from extronlib.engine import IpcpLink
link = IpcpLink('172.16.1.10','AVLAN')

from extronlib.system import Timer,SaveProgramLog


@Timer(10)
def t(timer,count):
    SaveProgramLog()
