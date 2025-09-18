from typing import Union
import socket


class ClientObject():
    """ This class provides a handle to connected clients to an EthernetServerInterfaceEx.

    Note:
        - This class cannot be instantiated by the programmer. It is only created by the `EthernetServerInterfaceEx` object.

    ---

    Parameters:
        - Hostname - Returns (string) - Hostname DNS name of the connection. Can be the IP Address
        - IPAddress - Returns (string) - the IP Address of the connected device
        - ServicePort - Returns (int) - ServicePort port on which the client will listen for data
    """


    def __init__(self):
        """ ClientObject class constructor. """
        self.__server = None #type:socket
        self._client_struct = {}
        self.Hostname = ''
        """Hostname DNS name of the connection. Can be the IP Address"""
        self.IPAddress = ''
        """the IP Address of the connected device"""
        self.ServicePort = ''
        """ServicePort port on which the client will listen for data"""

    def __eq__(self,other:'ClientObject'):
        if type(other) != ClientObject:
            return False
        a = '{}{}{}'.format(self.IPAddress,self.Hostname,self.ServicePort)
        b = '{}{}{}'.format(other.IPAddress,other.Hostname,other.ServicePort)
        return a == b

    def Disconnect(self):
        """ Closes the connection gracefully on client. """
        self.__server.close()

    def Send(self, data: 'bytes|str') -> None:
        """ Send string to the client.

        Arguments:
            - data (bytes, string) - string to send out

        Raises:
            - TypeError
            - IOError

        >>> client.Send(b'Hello.\n')
        """
        if type(data) == str:
            data = data.encode()
        self.__server.send(data)

    def _set_client(self,server,data):
        self._client_struct = data
        self.__server = server
        if 'IPAddress' in data:
            self.IPAddress=data['IPAddress']
        else:
            self.IPAddress=None
        if 'Hostname' in data:
            self.Hostname=data['Hostname']
        else:
            self.Hostname=None
        if 'ServicePort' in data:
            self.ServicePort=data['ServicePort']
        else:
            self.ServicePort=None

    def _recvfrom(self, bufsize):
        return self.__server.recvfrom(bufsize)

