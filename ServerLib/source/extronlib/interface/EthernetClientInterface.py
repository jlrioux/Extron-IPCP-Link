from extronlib.engine.IpcpLink import ExtronNode
import socket,time,re,time,paramiko
from threading import Thread,Lock
from datetime import datetime
from extronlib.system import Timer
import base64
_debug = False
import traceback




class _IPCPEthernetClientInterface(ExtronNode):
    """ This class provides an interface to a client ethernet socket. This class allows the user to send data over the ethernet port in a synchronous or asynchronous manner.

    Note: In synchronous mode, the user will use SendAndWait to wait for the response. In asynchronous mode, the user will assign a handler function to ReceiveData event handler. Then responses and unsolicited messages will be sent to the users receive data handler.

    Arguments:
        - Hostname (string) - DNS Name of the connection. Can be IP Address
        - IPPort (int) - IP port number of the connection
        - (optional) Protocol  (string) - Value for either 'TCP', 'UDP', or 'SSH'
        - (optional) ServicePort  (int) - Sets the port on which to listen for response data, UDP only, zero means listen on port OS assigns
        - (optional) Credentials  (tuple) - Username and password for SSH connection.

    Parameters:
        - Credentials - Returns (tuple, bool) - Username and password for SSH connection.
            - Note:
                - returns tuple: ('username', 'password') if provided otherwise None.
                - only applies when protocol 'SSH' is used.
        - Hostname - Returns (string) - server Host name
        - IPAddress - Returns (string) - server IP Address
        - IPPort - Returns (int) - IP port number of the connection
        - Protocol - Returns (string) - Value for either ’TCP’, ’UDP’, 'SSH' connection.
        - ServicePort - Returns (int) - the port on which the socket is listening for response data

    Events:
        - Connected - (Event) Triggers when socket connection is established.
        - Disconnected - (Event) Triggers when the socket connection is broken
        - ReceiveData - (Event) Receive Data event handler used for asynchronous transactions. The callback takes two arguments. The first one is the EthernetClientInterface instance triggering the event and the second one is a bytes string.
            - Note:
                - The maximum amount of data per ReceiveData event that will be passed into the handler is 1024 bytes. For payloads greater than 1024 bytes, multiple events will be triggered.
                - When UDP protocol is used, the data will be truncated to 1024 bytes.
    """

    _type='EthernetClientInterface'
    def __init__(self, Hostname, IPPort, Protocol='TCP', ServicePort=0, Credentials=None,bufferSize=4096,ipcp_index=0):
        """ EthernetClientInterface class constructor.

        Arguments:
            - Hostname (string) - DNS Name of the connection. Can be IP Address
            - IPPort (int) - IP port number of the connection
            - (optional) Protocol  (string) - Value for either 'TCP', 'UDP', or 'SSH'
            - (optional) ServicePort  (int) - Sets the port on which to listen for response data, UDP only, zero means listen on port OS assigns
            - (optional) Credentials  (tuple) - Username and password for SSH connection.
        """
        self.Connected = None
        self.Disconnected = None
        self.ReceiveData = None

        self.Hostname = Hostname
        self.IPPort = IPPort
        self.Protocol = Protocol
        self.ServicePort = ServicePort
        if Credentials == None:
            Credentials = ('','')
        self.Credentials = Credentials
        self.bufferSize = bufferSize



        self._args = [Hostname,IPPort,Protocol,ServicePort,list(Credentials)]
        self._ipcp_index = ipcp_index
        self._alias = f'ECI:{Hostname}:{IPPort}'
        self._callback_properties = {'Connected':None,
                                     'Disconnected':None,
                                     'ReceiveData':None}
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


    def Connect(self, timeout=None):
        """ Connect to the server

        Arguments:
            - (optional) timeout (float) - time in seconds to attempt connection before giving up.

        Returns
            - 'Connected' or 'ConnectedAlready' or reason for failure (string)

        Note: Does not apply to UDP connections.
        """
        return self._Query('Connect',[timeout])


    def Disconnect(self):
        """ Disconnect the socket

        Note: Does not apply to UDP connections.
        """
        self._Command('Disconnect',[])


    def Send(self, data:'str'):
        """ Send string over ethernet port if it’s open

        Arguments:
            - data (bytes, string) - string to send out

        Raises:
            - TypeError
            - IOError
        """
        if type(data) == str:
            data = data.encode()
        data = base64.b64encode(data).decode('utf-8')
        self._Command('Send',[data])



    def SendAndWait(self, data:'str', timeout:'float', deliTag:'bytes'='', deliRex:'str'='',deliLen:'int'=''):
        """ Send data to the controlled device and wait (blocking) for response. It returns after timeout seconds expires or immediately if the optional condition is satisfied.

        Note: In addition to data and timeout, the method accepts an optional delimiter, which is used to compare against the received response. It supports any one of the following conditions:
            -    > deliLen (int) - length of the response
            -    > deliTag (bytes) - suffix of the response
            -    > deliRex (regular expression object) - regular expression

        Note: The function will return an empty byte array if timeout expires and nothing is received, or the condition (if provided) is not met.

        Arguments:
            - data (bytes, string) - data to send.
            - timeout (float) - amount of time to wait for response.
            - delimiter (see above) - optional conditions to look for in response.

        Returns:
            - Response received data (may be empty) (bytes)
        """
        if type(data) == str:
            data = data.encode()
        data = base64.b64encode(data).decode('utf-8')
        if type(deliTag) == str:
            deliTag = deliTag.encode()
        if deliTag:
            deliTag = base64.b64encode(deliTag).decode('utf-8')
        res = self._Query('SendAndWait',[data,timeout,deliTag,deliRex,deliLen])
        return base64.b64decode(res)




    def StartKeepAlive(self, interval:'int', data:'bytes|str'):
        """ Repeatedly sends data at the given interval

        Arguments:
            - interval (float) - Time in seconds between transmissions
            - data (bytes, string) - data bytes to send
        """
        if type(data) == str:
            data = data.encode()
        data = base64.b64encode(data).decode('utf-8')
        self._Command('StartKeepAlive',[interval,data])


    def StopKeepAlive(self):
        """ Stop the currently running keep alive routine
        """
        self._Command('StopKeepAlive',[])

    def SetBufferSize(self,bufferSize):
        """ Sets the size of the RecieveData buffer for UDP communication. This is the largest single packet size that can be received.

        Parameters:
            - bufferSize (int) – Size of the buffer for ReceiveData
        """
        self.bufferSize = bufferSize
        self._Command('SetBufferSize',[bufferSize])













class _LocalEthernetClientInterface():
    """ This class provides an interface to a client ethernet socket. This class allows the user to send data over the ethernet port in a synchronous or asynchronous manner.

    Note: In synchronous mode, the user will use SendAndWait to wait for the response. In asynchronous mode, the user will assign a handler function to ReceiveData event handler. Then responses and unsolicited messages will be sent to the users receive data handler.

    Arguments:
        - Hostname (string) - DNS Name of the connection. Can be IP Address
        - IPPort (int) - IP port number of the connection
        - (optional) Protocol  (string) - Value for either 'TCP', 'UDP', or 'SSH'
        - (optional) ServicePort  (int) - Sets the port on which to listen for response data, UDP only, zero means listen on port OS assigns
        - (optional) Credentials  (tuple) - Username and password for SSH connection.

    Parameters:
        - Credentials - Returns (tuple, bool) - Username and password for SSH connection.
            - Note:
                - returns tuple: ('username', 'password') if provided otherwise None.
                - only applies when protocol 'SSH' is used.
        - Hostname - Returns (string) - server Host name
        - IPAddress - Returns (string) - server IP Address
        - IPPort - Returns (int) - IP port number of the connection
        - Protocol - Returns (string) - Value for either ’TCP’, ’UDP’, 'SSH' connection.
        - ServicePort - Returns (int) - the port on which the socket is listening for response data

    Events:
        - Connected - (Event) Triggers when socket connection is established.
        - Disconnected - (Event) Triggers when the socket connection is broken
        - ReceiveData - (Event) Receive Data event handler used for asynchronous transactions. The callback takes two arguments. The first one is the EthernetClientInterface instance triggering the event and the second one is a bytes string.
            - Note:
                - The maximum amount of data per ReceiveData event that will be passed into the handler is 1024 bytes. For payloads greater than 1024 bytes, multiple events will be triggered.
                - When UDP protocol is used, the data will be truncated to 1024 bytes.
    """

    def __init__(self, Hostname, IPPort, Protocol='TCP', ServicePort=0, Credentials=None):
        """ EthernetClientInterface class constructor.

        Arguments:
            - Hostname (string) - DNS Name of the connection. Can be IP Address
            - IPPort (int) - IP port number of the connection
            - (optional) Protocol  (string) - Value for either 'TCP', 'UDP', or 'SSH'
            - (optional) ServicePort  (int) - Sets the port on which to listen for response data, UDP only, zero means listen on port OS assigns
            - (optional) Credentials  (tuple) - Username and password for SSH connection.
        """
        self.Connected = None
        self.Disconnected = None
        self.ReceiveData = None

        self._socket = None #type:socket.socket|paramiko.SSHClient
        self._connected = False
        self._rec_thread = None
        self._rec_thread_stop = True
        self._send_and_wait_active = Lock()
        self._send_and_wait_rx = b''

        self._startkeepalive_timer = None #type:Timer

        self.Hostname = Hostname
        self.IPPort = IPPort
        self.Protocol = Protocol
        self.ServicePort = ServicePort
        self.Credentials = Credentials


        self._client = Client(self.Hostname)
        self._client.server = self
        self._client.IPAddress = self.Hostname

        if self.Protocol == 'UDP':
            try:
                self._socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                if self.ServicePort > 0:
                    self._socket.bind(('0.0.0.0',self.ServicePort))
                else:
                    self._socket.bind(('0.0.0.0',0))
                self._connected = True
                self._client.client = self._socket
            except Exception as e:
                print(f"UDP Socket error: {e}")



    def Connect(self, timeout=None):
        """ Connect to the server

        Arguments:
            - (optional) timeout (float) - time in seconds to attempt connection before giving up.

        Returns
            - 'Connected' or 'ConnectedAlready' or reason for failure (string)

        Note: Does not apply to UDP connections.
        """
        if self.Protocol == 'UDP':
            return('UDP:Connect Not Supported')
        if self._connected:
            return
        if self._connected:
            return('ConnectedAlready')
        if self.Protocol == 'TCP':
            try:
                self._socket = socket.create_connection((self.Hostname,self.IPPort),timeout)
            except:
                self._client.client = None
                return('Connection Timeout')
        elif self.Protocol == 'SSH':
            self._socket = paramiko.SSHClient()
            self._socket.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                self._socket.connect(self.Hostname,port=self.IPPort,username=self.Credentials[0],password=self.Credentials[1])
            except:
                self._client.client = None
                return('Connection Timeout')

        if self._socket is not None:
            self._connected = True
            self._client.client = self._socket
            if self.Protocol == 'TCP':
                self._rec_thread_stop = False
                self._rec_thread = Thread(target=self._recv_func(self._socket))
                self._rec_thread.start()
            if self.Connected is not None:
                self.Connected(self._client,'Connected')
            return('Connected')
        else:
            return('Connection Failed')

    def Disconnect(self):
        """ Disconnect the socket

        Note: Does not apply to UDP connections.
        """
        if self.Protocol == 'UDP':
            return('UDP:Disconnect Not Supported')
        self._rec_thread_stop = True
        if self._socket:
            self._socket.shutdown(socket.SHUT_RDWR)
            self._socket.close()
        if not self._connected:return
        self._connected = False
        self._socket = None
        if self.Disconnected is not None:
            self.Disconnected(self._client,'Disconnected')

    def Send(self, data:'str'):
        """ Send string over ethernet port if it’s open

        Arguments:
            - data (bytes, string) - string to send out

        Raises:
            - TypeError
            - IOError
        """
        if not self._connected:return
        if not self._socket:return
        if type(data) == str:
            data = data.encode('utf-8')
        try:
            if self.Protocol == 'UDP':
                self._socket.sendto(data,(self.Hostname,self.IPPort))
            else:
                self._socket.send(data)
        except Exception as e:
            if _debug:print('EthernetClientInterface.Send: Error :{}'.format(e))

    def SendAndWait(self, data:'str', timeout:'float', deliTag:'bytes'='', deliRex:'str'='',deliLen:'int'=''):
        """ Send data to the controlled device and wait (blocking) for response. It returns after timeout seconds expires or immediately if the optional condition is satisfied.

        Note: In addition to data and timeout, the method accepts an optional delimiter, which is used to compare against the received response. It supports any one of the following conditions:
            -    > deliLen (int) - length of the response
            -    > deliTag (bytes) - suffix of the response
            -    > deliRex (regular expression object) - regular expression

        Note: The function will return an empty byte array if timeout expires and nothing is received, or the condition (if provided) is not met.

        Arguments:
            - data (bytes, string) - data to send.
            - timeout (float) - amount of time to wait for response.
            - delimiter (see above) - optional conditions to look for in response.

        Returns:
            - Response received data (may be empty) (bytes)
        """
        if not self._socket:return(b'')
        if not self._connected:return(b'')
        self._send_and_wait_rx = b''
        if type(data) == str:
            data = data.encode('utf-8')
        self._send_and_wait_active.acquire()
        try:
            if self.Protocol == 'UDP':
                self._socket.sendto(data,(self.Hostname,self.IPPort))
            else:
                self._socket.send(data)
        except Exception as e:
            if _debug:print('EthernetClientInterface.SendAndWait: Error :{}'.format(e))
        starttime = datetime.now()
        buffer = b''
        while True:
            curtime = datetime.now()
            elapsed_time = curtime - starttime
            if elapsed_time.total_seconds() >= timeout:
                buffer = b''
                break
            if deliTag: #delimiter is bytes at which to stop reading
                delim = deliTag
                if delim in self._send_and_wait_rx:
                    index = self._send_and_wait_rx.index(delim)
                    buffer = self._send_and_wait_rx[:index+len(delim)]
                    break
            elif deliLen: #delimiter is a legnth to receive
                if len(self._send_and_wait_rx) >= deliLen:
                    buffer = self._send_and_wait_rx[:deliLen]
                    break
            elif deliRex: #delimiter should be a regular expression
                match = re.search(delim,self._send_and_wait_rx)
                if match is not None:
                    buffer = self._send_and_wait_rx[:match.end()]
                    break
            else:
                break
            time.sleep(0.01)
        self._send_and_wait_active.release()
        return(buffer)

    def StartKeepAlive(self, interval:'int', data:'bytes|str'):
        """ Repeatedly sends data at the given interval

        Arguments:
            - interval (float) - Time in seconds between transmissions
            - data (bytes, string) - data bytes to send
        """
        if self._startkeepalive_timer:
            self._startkeepalive_timer.Stop()
        if type(data) == str:
            data = data.encode('utf-8')
        def f(timer,count):
            if not self._connected:return
            if self._send_and_wait_active.locked():return
            try:
                if self.Protocol == 'UDP':
                    self._socket.sendto(data,(self.Hostname,self.IPPort))
                else:
                    self._socket.send(data)
            except Exception as e:
                if _debug:print('EthernetClientInterface.StartKeepAlive: Error :{}'.format(e))
        self._startkeepalive_timer = Timer(interval,f)

    def StopKeepAlive(self):
        """ Stop the currently running keep alive routine
        """
        if self._startkeepalive_timer:
            self._startkeepalive_timer.Stop()

    def _recv_func(self,client:'socket.socket'):
        def r():
            while True:
                if not self._connected:return
                if self._rec_thread_stop:return
                data = b''
                self._socket.settimeout(0.01)
                try:
                    if self.Protocol == 'UDP':
                        data,addr = self._socket.recvfrom(1024)
                    else:
                        data = self._socket.recv(1024)
                except TimeoutError:
                    pass
                except Exception as e:
                    if _debug:print('EthernetClientInterface._recv_func: Error :{}'.format(e))
                    self.Disconnect()
                if not self._send_and_wait_active.locked():
                    if self.ReceiveData is not None and len(data):
                        self.ReceiveData(self,data)
                else:
                    self._send_and_wait_rx += data
                time.sleep(0.01)
        return r
class Client():
    def __init__(self,hostname):
        self.IPAddress = hostname
        self.Hostname = hostname
        self.client = socket
        self.server = None
        def Send(self,data):
            if type(data) == str:
                data = data.encode('utf-8')
            try:
                self.client.Send(data)
            except ConnectionResetError:
                if self.Protocol != 'UDP':
                    if self.Disconnected is not None:
                        self.Disconnected(self._client,'Disconnected')
                    self.Disconnect()
                    self._connected = False
            except:
                pass










class EthernetClientInterface():
    """ EthernetClientInterface class constructor.

    Arguments:
        - Hostname (string) - DNS Name of the connection. Can be IP Address
        - IPPort (int) - IP port number of the connection
        - (optional) Protocol  (string) - Value for either 'TCP', 'UDP', or 'SSH'
        - (optional) ServicePort  (int) - Sets the port on which to listen for response data, UDP only, zero means listen on port OS assigns
        - (optional) Credentials  (tuple) - Username and password for SSH connection.
    """
    _type='EthernetClientInterface'
    def __init__(self, Hostname, IPPort, Protocol='TCP', ServicePort=0, Credentials=None,thru_ipcp=True,ipcp_index=0):
        self.Connected = None
        self.Disconnected = None
        self.ReceiveData = None

        self.Hostname = Hostname
        self.IPPort = IPPort
        self.Protocol = Protocol
        self.ServicePort = ServicePort
        if Credentials == None:
            Credentials = ('','')
        self.Credentials = Credentials
        self.__ECI = None
        if thru_ipcp:
            self.__ECI = _IPCPEthernetClientInterface(Hostname,IPPort,Protocol,ServicePort,Credentials,ipcp_index)
            self._type = self.__ECI._type
            self._args = [Hostname,IPPort,Protocol,ServicePort,list(Credentials)]
            self._ipcp_index = ipcp_index
            self._alias = f'ECI:{Hostname}:{IPPort}'
            self._initialize_values = self.__ECI._initialize_values
            self._UpdateResponse = self.__ECI._UpdateResponse
            self._Query = self.__ECI._Query
            self._Command = self.__ECI._Command
            self._QueryResponse = self.__ECI._QueryResponse
            self._InitResponse = self.__ECI._InitResponse
            self._ErrorResponse = self.__ECI._ErrorResponse
            self._Initialize = self.__ECI._Initialize
            self._LinkStatusChanged = self.__ECI._LinkStatusChanged
        else:
            self.__ECI = _LocalEthernetClientInterface(Hostname,IPPort,Protocol,ServicePort,Credentials)
        self.__subscribe_events()


    def __subscribe_events(self):
        def c(interface,state):
            if self.Connected:
                self.Connected(interface,state)
        self.__ECI.Connected = c
        def d(interface,state):
            if self.Disconnected:
                self.Disconnected(interface,state)
        self.__ECI.Disconnected = d
        def r(interface,data):
            if self.ReceiveData:
                self.ReceiveData(interface,data)
        self.__ECI.ReceiveData = r





    def Connect(self, timeout=None):
        """ Connect to the server

        Arguments:
            - (optional) timeout (float) - time in seconds to attempt connection before giving up.

        Returns
            - 'Connected' or 'ConnectedAlready' or reason for failure (string)

        Note: Does not apply to UDP connections.
        """
        return self.__ECI.Connect(timeout)


    def Disconnect(self):
        """ Disconnect the socket

        Note: Does not apply to UDP connections.
        """
        self.__ECI.Disconnect()


    def Send(self, data:'str'):
        """ Send string over ethernet port if it’s open

        Arguments:
            - data (bytes, string) - string to send out

        Raises:
            - TypeError
            - IOError
        """
        self.__ECI.Send(data)





    def SendAndWait(self, data:'str', timeout:'float', deliTag:'bytes'='', deliRex:'str'='',deliLen:'int'=''):
        """ Send data to the controlled device and wait (blocking) for response. It returns after timeout seconds expires or immediately if the optional condition is satisfied.

        Note: In addition to data and timeout, the method accepts an optional delimiter, which is used to compare against the received response. It supports any one of the following conditions:
            -    > deliLen (int) - length of the response
            -    > deliTag (bytes) - suffix of the response
            -    > deliRex (regular expression object) - regular expression

        Note: The function will return an empty byte array if timeout expires and nothing is received, or the condition (if provided) is not met.

        Arguments:
            - data (bytes, string) - data to send.
            - timeout (float) - amount of time to wait for response.
            - delimiter (see above) - optional conditions to look for in response.

        Returns:
            - Response received data (may be empty) (bytes)
        """
        return self.__ECI.SendAndWait(data,timeout,deliTag,deliRex,deliLen)



    def StartKeepAlive(self, interval:'int', data:'bytes|str'):
        """ Repeatedly sends data at the given interval

        Arguments:
            - interval (float) - Time in seconds between transmissions
            - data (bytes, string) - data bytes to send
        """
        self.__ECI.StartKeepAlive(interval,data)




    def StopKeepAlive(self):
        """ Stop the currently running keep alive routine
        """
        self.__ECI.StopKeepAlive()