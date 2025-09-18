from extronlib.engine.IpcpLink import ExtronNode
_debug = False
import traceback
import socket,base64,time
from threading import Thread
from extronlib.interface.ClientObject import ClientObject

class _IPCPEthernetServerInterfaceEx(ExtronNode):
    """ This class provides an interface to an Ethernet server that allows a user-defined amount of client connections. After instantiation, the server is started by calling StartListen(). This class allows the user to send data over the Ethernet port in an asynchronous manner using Send() and ReceiveData after a client has connected.

    ---

    Arguments:
        - IPPort  (int) - IP port number of the listening service.
        - (optional) Protocol  (string) - Value for either 'TCP' or 'UDP'
        - (optional) Interface  (string) - Defines the network interface on which to listen ('Any', 'LAN' of 'AVLAN')
        - (optional) MaxClients  (int) - maximum number of client connections to allow (None == Unlimited, 0 == Invalid)

    ---

    Parameters:
        - Clients - Returns (list of ClientObject) - List of connected clients.
        - IPPort - Returns (int) - IP Port number of the listening service
        - Interface - Returns (string) - name of interface on which the server is listening ('Any', 'LAN' of 'AVLAN')
        - MaxClients - Returns (int or None) - maximum number of client connections to allow (None == Unlimited, 0 == Invalid)
        - Protocol - Returns (string) - socket protocol ('TCP', 'UDP')

    ---

    Events:
        - Connected - (Event) Triggers when socket connection is established. The callback takes two arguments. The first one is the ClientObject instance triggering the event and the second one is a string ('Connected').
        - Disconnected - (Event) Triggers when the socket connection is broken. The callback takes two arguments. The first one is the ClientObject instance triggering the event and the second one is a string ('Disconnected').
        - ReceiveData - (Event) Receive Data event handler used for asynchronous transactions. The callback takes two arguments. The first one is the ClientObject instance triggering the event and the second one is a bytes string.
    """

    _type='EthernetServerInterfaceEx'
    def __init__(self, IPPort, Protocol='TCP', Interface='Any', MaxClients=None,ipcp_index=0):
        """ EthernetServerInterfaceEx class constructor.

        Arguments:
            - IPPort  (int) - IP port number of the listening service.
            - (optional) Protocol  (string) - Value for either 'TCP' or 'UDP'
            - (optional) Interface  (string) - Defines the network interface on which to listen
            - (optional) MaxClients  (int) - maximum number of client connections to allow (None == Unlimited, 0 == Invalid)
        """
        self.Connected = None
        self.Disconnected = None
        self.ReceiveData = None

        self.IPPort = IPPort
        self.Protocol = Protocol
        self.Interface = Interface
        self.MaxClients = MaxClients
        self.Clients = []



        self._args = [IPPort,Protocol,Interface,MaxClients]
        self._ipcp_index = ipcp_index
        self._alias = f'ESIEX:{Interface}:{IPPort}'
        self._callback_properties = {'Connected':None,
                                     'Disconnected':None,
                                     'ReceiveData':None}
        self._alt_callback_properties = ['Connected',
                                     'Disconnected',
                                     'ReceiveData']
        self._properties_to_reformat = ['ReceiveData']
        self._query_properties_init = {}
        self._query_properties_always = {}
        super().__init__(self)
        self._initialize_values()
    def _initialize_values(self):
        self._query_properties_init_list = list(self._query_properties_init.keys())
    def __format_parsed_update_value(self,property,value):
        if property in self._properties_to_reformat:
            if property == 'ReceiveData':
                if type(value) == list:
                    value = value[0]
                if type(value) == str:
                    value = value.encode()
                value = [base64.b64decode(value)]
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
                if property in self._alt_callback_properties:
                    prop = getattr(self,'_{}'.format(property))
                    if prop:
                        try:
                            value = self.__format_parsed_update_value(property,value)
                            prop(value[0],msg['qualifier'])
                        except Exception as e:
                            self.__OnError('Error calling {}.{} with exception: {}'.format(self._alias,property,traceback.format_exc()))
                else:
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





    def _Send(self,client:'ClientObject',data):
        if type(data) == str:
            data = data.encode()
        data = base64.b64encode(data).decode('utf-8')
        self._Command('Send',[client._client_struct,data])
    def _Connected(self,state,client_data):
        client = ClientObject()
        client._set_client(self,client_data)
        client_new = True
        for c in self.Clients:
            if c == client:
                client_new = False
        if client_new:
            self.Clients.append(client)
        if self.Connected:
            self.Connected(client,state)
    def _Disconnected(self,state,client_data):
        client = ClientObject()
        client._set_client(self,client_data)
        for c in self.Clients:
            if c == client:
                self.Clients.remove(c)
        if self.Disconnected:
            self.Disconnected(client,state)
    def _ReceiveData(self,data,client_data):
        client = ClientObject()
        client._set_client(self,client_data)
        client_new = True
        for c in self.Clients:
            if c == client:
                client_new = False
        if client_new:
            self.Clients.append(client)
        if self.ReceiveData:
            self.ReceiveData(client,data)


    def Disconnect(self, client:'ClientObject'):
        """ Closes the connection gracefully on specified client.

        Arguments:
            - client (ClientObject) - handle to client object
        """
        self._Command('Disconnect',[client._client_struct])

    def StartListen(self, timeout=0):
        """ Start the listener

        Arguments:
            - (optional) timeout  (float) - how long to listen for connections (0=Forever)

        Returns:
            - 'Listening' or a reason for failure (e.g. 'PortUnavailable')

        Raises:
            - IOError

        Note: Return examples:
            - Listening
            - ListeningAlready
            - PortUnavailable
            - InterfaceUnavailable: LAN
            - InterfaceUnavailable: LAN, AVLAN

        Note: If 'Listening' not in result, the server will not be listening.
        """
        return self._Query('StartListen',[timeout])

    def StopListen(self):
        """ Stop the listener
        """
        self._Command('StopListen',[])


    def SSLWrap(self,certificate:'str'=None,cert_reqs:'str'='CERT_REQUIRED',ssl_versiion:'str'='TLSv2',ca_certs:'str'=None):
        '''
        Wrap all connections to this server instance in an SSL context.

        Note
        This is almost a direct call to ssl.wrap_socket(). See python documentation for more details. The following changes are applied:

            - Property server_side is set to True
            - Property cert_reqs is a string
            - Property ssl_version is a string
            - Property do_handshake_on_connect is set to True
            - Property suppress_ragged_eofs is set to True
            - Property ciphers is fixed to the system default
        Parameters:
            - certificate (string) – alias to a specific keyfile/certificate pair
            - cert_reqs (string) – specifies whether a certificate is required from the other side of the connection ('CERT_NONE', 'CERT_OPTIONAL', or 'CERT_REQUIRED'). If the value of this parameter is not 'CERT_NONE', then the ca_certs parameter must point to a file of CA certificates.
            - ssl_version (string) – version from the supported SSL/TLS version table ('TLSv2'). Currently only TLS 1.2 is allowed.
            - ca_certs (string) – alias to a file that contains a set of concatenated “certification authority” certificates, which are used to validate certificates passed from the other end of the connection.
        Note
            - Requires protocol 'TCP'.
            - certificate and ca_certs specify aliases to machine certificate/key pairs and CA certificates uploaded to the processor in Toolbelt.
        '''
        self._Command('SSLWrap',[certificate,cert_reqs,ssl_versiion,ca_certs])








'''
    TODO : enforce if SSLWrap is used, host on remote ipcp, maybe thru ipcp should be default behavior?


'''
class _LocalEthernetServerInterfaceEx():
    """ This class provides an interface to an Ethernet server that allows a user-defined amount of client connections. After instantiation, the server is started by calling StartListen(). This class allows the user to send data over the Ethernet port in an asynchronous manner using Send() and ReceiveData after a client has connected.

    ---

    Arguments:
        - IPPort  (int) - IP port number of the listening service.
        - (optional) Protocol  (string) - Value for either 'TCP' or 'UDP'
        - (optional) Interface  (string) - Defines the network interface on which to listen ('Any', 'LAN' of 'AVLAN')
        - (optional) MaxClients  (int) - maximum number of client connections to allow (None == Unlimited, 0 == Invalid)

    ---

    Parameters:
        - Clients - Returns (list of ClientObject) - List of connected clients.
        - IPPort - Returns (int) - IP Port number of the listening service
        - Interface - Returns (string) - name of interface on which the server is listening ('Any', 'LAN' of 'AVLAN')
        - MaxClients - Returns (int or None) - maximum number of client connections to allow (None == Unlimited, 0 == Invalid)
        - Protocol - Returns (string) - socket protocol ('TCP', 'UDP')

    ---

    Events:
        - Connected - (Event) Triggers when socket connection is established. The callback takes two arguments. The first one is the ClientObject instance triggering the event and the second one is a string ('Connected').
        - Disconnected - (Event) Triggers when the socket connection is broken. The callback takes two arguments. The first one is the ClientObject instance triggering the event and the second one is a string ('Disconnected').
        - ReceiveData - (Event) Receive Data event handler used for asynchronous transactions. The callback takes two arguments. The first one is the ClientObject instance triggering the event and the second one is a bytes string.
    """

    def __init__(self, IPPort, Protocol='TCP', Interface='Any', MaxClients=None):
        """ EthernetServerInterfaceEx class constructor.

        Arguments:
            - IPPort  (int) - IP port number of the listening service.
            - (optional) Protocol  (string) - Value for either 'TCP' or 'UDP'
            - (optional) Interface  (string) - Defines the network interface on which to listen
            - (optional) MaxClients  (int) - maximum number of client connections to allow (None == Unlimited, 0 == Invalid)
        """
        self.Clients = []#type:list[ClientObject]
        self.Connected = None
        self.Disconnected = None
        self.ReceiveData = None

        self.__socket = None #type:socket.socket
        self.__islistening = False
        self.__isbound = False

        self.__recv_threads = [] #type:list[Thread]
        self.__accept_thread = None #type:Thread

        self.IPPort = IPPort
        self.Protocol = Protocol
        self.Interface = Interface
        self.MaxClients = MaxClients

        if self.MaxClients == None:
            self.MaxClients = 100

        if(self.Protocol == 'UDP'):
            self.__socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        elif(self.Protocol == 'TCP'):
            self.__socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        else:
            print('EthernetServerInterfaceEx: Error: Invalid Protocol:',str(Protocol))
        self.__socket.bind(('localhost',self.IPPort))
        self.__isbound = True

        if self.Protocol == 'TCP':
            self.__accept_thread = Thread(target=self.__accept_func)
            self.__accept_thread.start()

    def Send(self,data:'str'):
        if self.Protocol == 'TCP':
            if not self.__isbound:
                return
            self.__socket.send(data)
            return
            for client in self.Clients:
                try:
                    print('sending packet')
                    client.Send(data)
                except Exception as e:
                    print('error sending packet:{}'.format(e))

    def Disconnect(self, client:'ClientObject'):
        """ Closes the connection gracefully on specified client.

        Arguments:
            - client (ClientObject) - handle to client object
        """
        if not self.__isbound:
            return
        #self.__islistening = False
        if self.Protocol == 'TCP':
            if self.Disconnected is not None:
                if client in self.Clients:
                    self.Clients.remove(client)
                    client.Disconnect()
                    self.Disconnected(client,'Disconnected')

    def StartListen(self, timeout=0):
        """ Start the listener

        Arguments:
            - (optional) timeout  (float) - how long to listen for connections (0=Forever)

        Returns:
            - 'Listening' or a reason for failure (e.g. 'PortUnavailable')

        Raises:
            - IOError

        Note: Return examples:
            - Listening
            - ListeningAlready
            - PortUnavailable
            - InterfaceUnavailable: LAN
            - InterfaceUnavailable: LAN, AVLAN

        Note: If 'Listening' not in result, the server will not be listening.
        """
        if not self.__isbound:
            return
        try:
            self.__socket.listen()
        except Exception as e:
            print('failed to listen on socket for port{}:{}'.format(self.IPPort,e))
            return 'Not Listening'
        self.__islistening = True
        return 'Listening'

    def StopListen(self):
        """ Stop the listener
        """
        if not self.__isbound:
            return
        self.__socket.close()
        self.__islistening = False

    def SSLWrap(self,certificate:'str'=None,cert_reqs:'str'='CERT_REQUIRED',ssl_versiion:'str'='TLSv2',ca_certs:'str'=None):
        '''
        Wrap all connections to this server instance in an SSL context.

        Note
        This is almost a direct call to ssl.wrap_socket(). See python documentation for more details. The following changes are applied:

            - Property server_side is set to True
            - Property cert_reqs is a string
            - Property ssl_version is a string
            - Property do_handshake_on_connect is set to True
            - Property suppress_ragged_eofs is set to True
            - Property ciphers is fixed to the system default
        Parameters:
            - certificate (string) – alias to a specific keyfile/certificate pair
            - cert_reqs (string) – specifies whether a certificate is required from the other side of the connection ('CERT_NONE', 'CERT_OPTIONAL', or 'CERT_REQUIRED'). If the value of this parameter is not 'CERT_NONE', then the ca_certs parameter must point to a file of CA certificates.
            - ssl_version (string) – version from the supported SSL/TLS version table ('TLSv2'). Currently only TLS 1.2 is allowed.
            - ca_certs (string) – alias to a file that contains a set of concatenated “certification authority” certificates, which are used to validate certificates passed from the other end of the connection.
        Note
            - Requires protocol 'TCP'.
            - certificate and ca_certs specify aliases to machine certificate/key pairs and CA certificates uploaded to the processor in Toolbelt.
        '''
        pass

    def __accept_func(self):
        while True:
            try:
                conn,addr = self.__socket.accept()
            except Exception as e:
                print('Error accepting connection:{}'.format(e))
                continue
            client = ClientObject()
            data = {'IPAddress':addr[0],'Hostname':addr[0],'ServicePort':addr[1]}
            client._set_client(conn,data)
            self.Clients.append(client)
            self.__recv_threads.append(Thread(target=self.__recv_func(client)))
            self.__recv_threads[-1].start()
            if self.Connected is not None:
                self.Connected(client,'Connected')

    def __recv_func(self,client):
        def r():
            while True:
                time.sleep(0.01)
                if self.__islistening and len(self.Clients):
                    try:
                        data,address = client._recvfrom(1024)
                    except:
                        data = b''
                        address = ''
                    if self.ReceiveData is not None and len(data):
                        self.ReceiveData(client,data)
                    if len(data) < 1:
                        while client in self.Clients:
                            self.Clients.remove(client)
                        if self.Disconnected is not None:
                            self.Disconnected(client,'Disconnected')
                        return
        return r








class EthernetServerInterfaceEx():
    """ This class provides an interface to an Ethernet server that allows a user-defined amount of client connections. After instantiation, the server is started by calling StartListen(). This class allows the user to send data over the Ethernet port in an asynchronous manner using Send() and ReceiveData after a client has connected.

    ---

    Arguments:
        - IPPort  (int) - IP port number of the listening service.
        - (optional) Protocol  (string) - Value for either 'TCP' or 'UDP'
        - (optional) Interface  (string) - Defines the network interface on which to listen ('Any', 'LAN' of 'AVLAN')
        - (optional) MaxClients  (int) - maximum number of client connections to allow (None == Unlimited, 0 == Invalid)

    ---

    Parameters:
        - Clients - Returns (list of ClientObject) - List of connected clients.
        - IPPort - Returns (int) - IP Port number of the listening service
        - Interface - Returns (string) - name of interface on which the server is listening ('Any', 'LAN' of 'AVLAN')
        - MaxClients - Returns (int or None) - maximum number of client connections to allow (None == Unlimited, 0 == Invalid)
        - Protocol - Returns (string) - socket protocol ('TCP', 'UDP')

    ---

    Events:
        - Connected - (Event) Triggers when socket connection is established. The callback takes two arguments. The first one is the ClientObject instance triggering the event and the second one is a string ('Connected').
        - Disconnected - (Event) Triggers when the socket connection is broken. The callback takes two arguments. The first one is the ClientObject instance triggering the event and the second one is a string ('Disconnected').
        - ReceiveData - (Event) Receive Data event handler used for asynchronous transactions. The callback takes two arguments. The first one is the ClientObject instance triggering the event and the second one is a bytes string.
    """

    def __init__(self, IPPort, Protocol='TCP', Interface='Any', MaxClients=None,thru_ipcp=False,ipcp_index=0):
        """ EthernetServerInterfaceEx class constructor.

        Arguments:
            - IPPort  (int) - IP port number of the listening service.
            - (optional) Protocol  (string) - Value for either 'TCP' or 'UDP'
            - (optional) Interface  (string) - Defines the network interface on which to listen
            - (optional) MaxClients  (int) - maximum number of client connections to allow (None == Unlimited, 0 == Invalid)
        """
        self.Clients = []#type:list[ClientObject]
        self.IPPort = IPPort
        self.Protocol = Protocol
        self.Interface = Interface
        self.MaxClients = MaxClients

        self.Connected = None
        self.Disconnected = None
        self.ReceiveData = None


        self.__ESIEX = None
        if thru_ipcp:
            self.__ESIEX = _IPCPEthernetServerInterfaceEx(IPPort,Protocol,Interface,MaxClients,ipcp_index)
            self._type = self.__ESIEX._type
            self._ipcp_index = ipcp_index
            self._alias = f'ESIEX:{Interface}:{IPPort}'
            self._initialize_values = self.__ESIEX._initialize_values
            self._UpdateResponse = self.__ESIEX._UpdateResponse
            self._Query = self.__ESIEX._Query
            self._Command = self.__ESIEX._Command
            self._QueryResponse = self.__ESIEX._QueryResponse
            self._InitResponse = self.__ESIEX._InitResponse
            self._ErrorResponse = self.__ESIEX._ErrorResponse
            self._Initialize = self.__ESIEX._Initialize
            self._LinkStatusChanged = self.__ESIEX._LinkStatusChanged
            self.Clients = self.__ESIEX.Clients
            self.Disconnect = self.__ESIEX.Disconnect
            self.StartListen = self.__ESIEX.StartListen
            self.StopListen = self.__ESIEX.StopListen
            self.SSLWrap = self.__ESIEX.SSLWrap
            self.Send = self.__ESIEX.Send
        else:
            self.__ESIEX = _LocalEthernetServerInterfaceEx(IPPort,Protocol,Interface,MaxClients)
            self.Clients = self.__ESIEX.Clients
            self.Disconnect = self.__ESIEX.Disconnect
            self.StartListen = self.__ESIEX.StartListen
            self.StopListen = self.__ESIEX.StopListen
            self.SSLWrap = self.__ESIEX.SSLWrap
            self.Send = self.__ESIEX.Send
        self.__subscribe_events()


    def __subscribe_events(self):
        def c(interface,state):
            if self.Connected:
                self.Connected(interface,state)
        self.__ESIEX.Connected = c
        def d(interface,state):
            if self.Disconnected:
                self.Disconnected(interface,state)
        self.__ESIEX.Disconnected = d
        def r(interface,data):
            if self.ReceiveData:
                self.ReceiveData(interface,data)
        self.__ESIEX.ReceiveData = r



