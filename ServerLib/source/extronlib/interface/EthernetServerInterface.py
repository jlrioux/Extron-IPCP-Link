from extronlib.engine.IpcpLink import ExtronNode
_debug = False
import traceback

import socket,time,re,time,paramiko,base64
from threading import Thread,Lock
from datetime import datetime
from extronlib.system import Timer


class _IPCPEthernetServerInterface(ExtronNode):
    """ This class provides an interface to a server Ethernet socket. After instantiation, the server is started by calling StartListen(). This class allows the user to send data over the Ethernet port in an asynchronous manner using Send() and ReceiveData after a client has connected.

    :Warning:: This class is no longer supported. For any new development, EthernetServerInterfaceEx should be used.

    ---

    Arguments:
        - IPPort  (int) - IP port number of the listening service.
        - (optional) Protocol  (string) - Value for either 'TCP' or 'UDP'
        - (optional) Interface  (string) - Defines the network interface on which to listen ('Any', 'LAN' of 'AVLAN')
        - (optional) ServicePort  (int) - sets the port from which the client will send data. Zero means any service port is valid.

    Note: ServicePort is only applicable to 'UDP' protocol type.

    ---

    Parameters:
        - Hostname - Returns (string) - Hostname DNS name of the connection. Can be the IP Address
        - IPAddress - Returns (string) - the IP Address of the connected device
        - IPPort - Returns (int) - IP Port number of the listening service
        - Interface - Returns (string) - name of interface on which the server is listening
        - Protocol - Returns (string) - Value for either ’TCP’, ’UDP’ connection.
        - ServicePort - Returns (int) - ServicePort port on which the client will listen for data

    ---

    Events:
        - Connected - (Event) Triggers when socket connection is established.
        - Disconnected - (Event) Triggers when the socket connection is broken
        - ReceiveData - (Event) Receive Data event handler used for asynchronous transactions. The callback takes two arguments. The first one is the EthernetServerInterface instance triggering the event and the second one is a bytes string.
    """


    _type='EthernetServerInterface'
    def __init__(self, IPPort, Protocol='TCP', Interface='Any', ServicePort=0,ipcp_index=0):
        """ EthernetServerInterface class constructor.

        Arguments:
            - IPPort  (int) - IP port number of the listening service.
            - (optional) Protocol  (string) - Value for either 'TCP' or 'UDP'
            - (optional) Interface  (string) - Defines the network interface on which to listen ('Any', 'LAN' of 'AVLAN')
            - (optional) ServicePort  (int) - sets the port from which the client will send data. Zero means any service port is valid.
        """
        self.IPPort = IPPort
        self.Protocol = Protocol
        self.Interface = Interface
        self.ServicePort = ServicePort
        self.Connected = False
        self.Disconnected = True
        self.HostName = ''
        self.IPAddress = ''
        self.ReceiveData = None


        self._args = [IPPort,Protocol,Interface,ServicePort]
        self._ipcp_index = ipcp_index
        self._alias = f'ESI:{Interface}:{IPPort}'
        self._callback_properties = {'Connected':None,
                                     'Disconnected':None,
                                     'ReceiveData':None}
        self._properties_to_reformat = ['ReceiveData']
        self._query_properties_init = {}
        self._query_properties_always = {'HostName':None,
                                         'IPAddress':None}
        super().__init__(self)
        self._initialize_values()
    def _initialize_values(self):
        self._query_properties_init_list = list(self._query_properties_init.keys())
    def __format_parsed_update_value(self,property,value):
        if property in self._properties_to_reformat:
            if property == 'ReceiveData':
                if type(value) == list:
                    value = value[0]
                value = base64.b64decode(value)
            if _debug:print(f'{self._alias}: reformatted value of {property} to {value}')
        return value
    def _Parse_Update(self,msg_in):
        msg_type = msg_in['type']
        if _debug:print(f'got message type {msg_type} for alias {self._alias}')
        if msg_type == 'init':return
        msg = msg_in['message']
        property = msg['property']
        value = msg['value']
        if msg_type == 'update':
            if property in self._callback_properties:
                prop = getattr(self,property)
                if prop:
                    try:
                        if self._callback_properties[property] != None:setattr(self,self._callback_properties[property]['var'],value[self._callback_properties[property]['value index']])
                        value = self.__format_parsed_update_value(property,value)
                        prop(self,*value)
                    except Exception as e:
                        self.__OnError('Error calling {}.{} with exception: {}'.format(self._alias,property,traceback.format_exc()))
        elif msg_type == 'query':
            try:
                self._locks_values[msg_in['query id']] = self.__format_parsed_update_value(property,value)
            except Exception as e:
                self.__OnError('Error setting {}.{} with exception: {}'.format(self._alias,property,traceback.format_exc()))
            if _debug:print('{}:set query attribute {} to {}'.format(self._alias,property,value))
        elif msg_type == 'error':
            if 'query id' in msg_in:
                try:
                    self._locks_values[msg_in['query id']] = value
                except Exception as e:
                    self.__OnError('Error setting {}.{} with exception: {}'.format(self._alias,property,traceback.format_exc()))
                self.__OnError('{}:error on query attribute {}'.format(self._alias,property))
            elif 'qualifier' in msg:
                self.__OnError('{}:error on attribute {} with {}'.format(self._alias,property,msg['qualifier']))
                if property == 'init':
                    self._release_lock(property)
        else:
            try:
                setattr(self,property,self.__format_parsed_update_value(property,value))
            except Exception as e:
                self.__OnError('Error setting {}.{} with exception: {}'.format(self._alias,property,traceback.format_exc()))
            if _debug:print('{}:set attribute {} to {}'.format(self._alias,property,value))
    def __OnError(self,msg):
        from datetime import datetime
        print(f'{datetime.now()}: {self._alias}: {msg}')

    def Disconnect(self):
        """ Closes the connection gracefully.
        """
        self._Command('Disconnect',[])


    def Send(self, data):
        """ Send string over ethernet port if it’s open

        Arguments:
            - data  (int) - string to send out

        Raises:
            - TypeError
            - IOError
        """
        if type(data) == str:
            data = data.encode()
        data = base64.b64encode(data).decode('utf-8')
        self._Command('Send',[data])


    def StartListen(self, timeout=0):
        """ Start the listener

        Arguments:
            - (optional) timeout  (float) - how long to listen for connections (0=Forever)

        Returns:
            - 'Listening' or a reason for failure (e.g. 'PortUnavailable')

        Raises:
            - IOError
        """
        self._Command('StartListen',[timeout])

    def StopListen(self):
        """ Stop the listener
        """
        self._Command('StopListen',[])







class _LocalEthernetServerInterface():
    """ This class provides an interface to a server Ethernet socket. After instantiation, the server is started by calling StartListen(). This class allows the user to send data over the Ethernet port in an asynchronous manner using Send() and ReceiveData after a client has connected.

    :Warning:: This class is no longer supported. For any new development, EthernetServerInterfaceEx should be used.

    ---

    Arguments:
        - IPPort  (int) - IP port number of the listening service.
        - (optional) Protocol  (string) - Value for either 'TCP' or 'UDP'
        - (optional) Interface  (string) - Defines the network interface on which to listen ('Any', 'LAN' of 'AVLAN')
        - (optional) ServicePort  (int) - sets the port from which the client will send data. Zero means any service port is valid.

    Note: ServicePort is only applicable to 'UDP' protocol type.

    ---

    Parameters:
        - Hostname - Returns (string) - Hostname DNS name of the connection. Can be the IP Address
        - IPAddress - Returns (string) - the IP Address of the connected device
        - IPPort - Returns (int) - IP Port number of the listening service
        - Interface - Returns (string) - name of interface on which the server is listening
        - Protocol - Returns (string) - Value for either ’TCP’, ’UDP’ connection.
        - ServicePort - Returns (int) - ServicePort port on which the client will listen for data

    ---

    Events:
        - Connected - (Event) Triggers when socket connection is established.
        - Disconnected - (Event) Triggers when the socket connection is broken
        - ReceiveData - (Event) Receive Data event handler used for asynchronous transactions. The callback takes two arguments. The first one is the EthernetServerInterface instance triggering the event and the second one is a bytes string.
    """



    def __init__(self, IPPort, Protocol='TCP', Interface='Any', ServicePort=0):
        """ EthernetServerInterface class constructor.

        Arguments:
            - IPPort  (int) - IP port number of the listening service.
            - (optional) Protocol  (string) - Value for either 'TCP' or 'UDP'
            - (optional) Interface  (string) - Defines the network interface on which to listen ('Any', 'LAN' of 'AVLAN')
            - (optional) ServicePort  (int) - sets the port from which the client will send data. Zero means any service port is valid.
        """
        self.IPPort = IPPort
        self.Protocol = Protocol
        self.Interface = Interface
        self.ServicePort = ServicePort
        self.Connected = False
        self.Disconnected = True
        self.HostName = ''
        self.IPAddress = ''
        self.ReceiveData = None

    def Disconnect(self):
        """ Closes the connection gracefully.
        """
        pass

    def Send(self, data):
        """ Send string over ethernet port if it’s open

        Arguments:
            - data  (int) - string to send out

        Raises:
            - TypeError
            - IOError
        """
        pass

    def StartListen(self, timeout=0):
        """ Start the listener

        Arguments:
            - (optional) timeout  (float) - how long to listen for connections (0=Forever)

        Returns:
            - 'Listening' or a reason for failure (e.g. 'PortUnavailable')

        Raises:
            - IOError
        """
        pass

    def StopListen(self):
        """ Stop the listener
        """
        pass





class EthernetServerInterface():
    """ This class provides an interface to a server Ethernet socket. After instantiation, the server is started by calling StartListen(). This class allows the user to send data over the Ethernet port in an asynchronous manner using Send() and ReceiveData after a client has connected.

    :Warning:: This class is no longer supported. For any new development, EthernetServerInterfaceEx should be used.

    ---

    Arguments:
        - IPPort  (int) - IP port number of the listening service.
        - (optional) Protocol  (string) - Value for either 'TCP' or 'UDP'
        - (optional) Interface  (string) - Defines the network interface on which to listen ('Any', 'LAN' of 'AVLAN')
        - (optional) ServicePort  (int) - sets the port from which the client will send data. Zero means any service port is valid.

    Note: ServicePort is only applicable to 'UDP' protocol type.

    ---

    Parameters:
        - Hostname - Returns (string) - Hostname DNS name of the connection. Can be the IP Address
        - IPAddress - Returns (string) - the IP Address of the connected device
        - IPPort - Returns (int) - IP Port number of the listening service
        - Interface - Returns (string) - name of interface on which the server is listening
        - Protocol - Returns (string) - Value for either ’TCP’, ’UDP’ connection.
        - ServicePort - Returns (int) - ServicePort port on which the client will listen for data

    ---

    Events:
        - Connected - (Event) Triggers when socket connection is established.
        - Disconnected - (Event) Triggers when the socket connection is broken
        - ReceiveData - (Event) Receive Data event handler used for asynchronous transactions. The callback takes two arguments. The first one is the EthernetServerInterface instance triggering the event and the second one is a bytes string.
    """



    def __init__(self, IPPort, Protocol='TCP', Interface='Any', ServicePort=0,thru_ipcp=True,ipcp_index=0):
        """ EthernetServerInterface class constructor.

        Arguments:
            - IPPort  (int) - IP port number of the listening service.
            - (optional) Protocol  (string) - Value for either 'TCP' or 'UDP'
            - (optional) Interface  (string) - Defines the network interface on which to listen ('Any', 'LAN' of 'AVLAN')
            - (optional) ServicePort  (int) - sets the port from which the client will send data. Zero means any service port is valid.
        """
        self.IPPort = IPPort
        self.Protocol = Protocol
        self.Interface = Interface
        self.ServicePort = ServicePort
        self.Connected = False
        self.Disconnected = True
        #self.HostName = ''
        #self.IPAddress = ''
        self.ReceiveData = None

        self.__ESI = None
        if thru_ipcp:
            self.__ESI = _IPCPEthernetServerInterface(IPPort,Protocol,Interface,ServicePort,ipcp_index)
            self._type = self.__ESI._type
            self._ipcp_index = ipcp_index
            self._alias = f'ESI:{Interface}:{IPPort}'
            self._initialize_values = self.__ESI._initialize_values
            self._UpdateResponse = self.__ESI._UpdateResponse
            self._Query = self.__ESI._Query
            self._Command = self.__ESI._Command
            self._QueryResponse = self.__ESI._QueryResponse
            self._InitResponse = self.__ESI._InitResponse
            self._ErrorResponse = self.__ESI._ErrorResponse
            self._Initialize = self.__ESI._Initialize
            self._LinkStatusChanged = self.__ESI._LinkStatusChanged
        else:
            self.__ESI = _LocalEthernetServerInterface(IPPort,Protocol,Interface,ServicePort)
        self.__subscribe_events()


    def __subscribe_events(self):
        def c(interface,state):
            if self.Connected:
                self.Connected(interface,state)
        self.__ESI.Connected = c
        def d(interface,state):
            if self.Disconnected:
                self.Disconnected(interface,state)
        self.__ESI.Disconnected = d
        def r(interface,data):
            if self.ReceiveData:
                self.ReceiveData(interface,data)
        self.__ESI.ReceiveData = r


    @property
    def HostName(self):
        return self.__ESI.HostName


    @property
    def IPAddress(self):
        return self.__ESI.IPAddress




    def Disconnect(self):
        """ Closes the connection gracefully.
        """
        self.__ESI.Disconnect()


    def Send(self, data):
        """ Send string over ethernet port if it’s open

        Arguments:
            - data  (int) - string to send out

        Raises:
            - TypeError
            - IOError
        """
        self.__ESI.Send(data)



    def StartListen(self, timeout=0):
        """ Start the listener

        Arguments:
            - (optional) timeout  (float) - how long to listen for connections (0=Forever)

        Returns:
            - 'Listening' or a reason for failure (e.g. 'PortUnavailable')

        Raises:
            - IOError
        """
        self.__ESI.StartListen(timeout)



    def StopListen(self):
        """ Stop the listener
        """
        self.__ESI.StopListen()


