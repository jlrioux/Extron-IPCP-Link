


from extronlib.interface import EthernetServerInterfaceEx
from extronlib.system import Timer

i = EthernetServerInterfaceEx(2023)
res = i.StartListen()
print('listen result:{}'.format(res))
connected = False

def rx(interface,data):
    print('recieved:{}'.format(data))
    i.Send(b'got it\r\n')
    if data == b'd':
        i.Disconnect()
i.ReceiveData = rx

def c(*args):
    global connected
    connected = True
    print('connected')
i.Connected = c

def d(*args):
    global connected
    connected = False
    print('disconnected')
i.Disconnected = d


@Timer(10)
def t2(timer,count):
    i.Send(b'ping\r\n')






