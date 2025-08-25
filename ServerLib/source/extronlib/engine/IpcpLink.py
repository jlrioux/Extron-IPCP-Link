import re,json,threading,time,socket,queue
from extronlib.system import Timer
from datetime import datetime
import pickle,base64

_debug = False
import traceback
class ExtronNode():
    def __init__(self,obj):
        self._locks = {} #type:dict[str,threading.Lock]
        self._locks_lock = threading.Lock()
        self._locks_values = {}
        self.__query_id = 0
        self.ipcp_link = IpcpLink.ipcp_links[self._ipcp_index]
        IpcpLink.RegisterNode(self)
        self.LinkStatusCallback = None
        self.LinkStatus = 'Disconnected'
        self._Initialize()



    def __aquire_lock(self,key=None):
        with self._locks_lock:
            self.__query_id += 1
            if key == None:
                key = self.__query_id
            if key not in self._locks:
                self._locks[key] = threading.Lock()
        self._locks[key].acquire()
        return key
    def __release_lock(self,key):
        if key in self._locks:
            if self._locks[key].locked():
                self._locks[key].release()
    def _release_all_locks(self):
        for key in self._locks:
            if self._locks[key].locked():
                self._locks[key].release()
    def _release_lock(self,key):self.__release_lock(key)

    def _Command(self,property,args):
        msg = f"{self._alias}~~{json.dumps({'type':'command','device type':self._type,'property':property,'args':args})}"
        self.ipcp_link.Command(msg)

    def _Query(self,property,args):
        key = self.__aquire_lock()
        msg = f"{self._alias}~~{json.dumps({'type':'query','query id':key,'device type':self._type,'property':property,'args':args})}"
        self.ipcp_link.Query(msg)
        while self._locks[key].locked():
            time.sleep(0.001)
        try:
            value = self._locks_values[key]
        except:
            value = None
        with self._locks_lock:
            try:
                del self._locks_values[key]
            except:
                pass
            try:
                del self._locks[key]
            except:
                pass
        return value

    def _QueryResponse(self,msg):
        self._Parse_Update(msg)
        if msg['query id'] in self._locks:self.__release_lock(msg['query id'])
    def _ErrorResponse(self,msg):
        self._Parse_Update(msg)
        if 'query id' in msg:
           if msg['query id'] in self._locks:self.__release_lock(msg['query id'])
    def _UpdateResponse(self,msg):
        self._Parse_Update(msg)
    def _InitResponse(self,msg):
        self._Parse_Update(msg)
        self.__release_lock('init')
    def _Initialize(self):
        msg = f"{self._alias}~~{json.dumps({'type':'init','device type':self._type,'args':self._args})}"
        self.ipcp_link.Init(msg)
        key = self.__aquire_lock('init')
        while self._locks[key].locked():
            time.sleep(0.001)
        with self._locks_lock:
            del self._locks['init']
        self._initialize_values()

    def _LinkStatusChanged(self,value):
        self.LinkStatus = value
        self._release_all_locks()
        if self.LinkStatusCallback:
                self.LinkStatusCallback(value)

socket.getaddrinfo('localhost',8080)
class _EthernetClientSimple():
    def __init__(self, Hostname:'str', IPPort:'int', Protocol='TCP', ServicePort=0, Credentials=None):
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

        self.__socket = None #type:socket.socket
        self.__connected = False
        self.__rec_thread = None
        self.__rec_thread_stop = True

        self.Hostname = Hostname
        self.IPPort = IPPort
        self.Protocol = Protocol
        self.ServicePort = ServicePort
        self.Credentials = Credentials

    def Connect(self, timeout=None):
        """ Connect to the server

        Arguments:
            - (optional) timeout (float) - time in seconds to attempt connection before giving up.

        Returns
            - 'Connected' or 'ConnectedAlready' or reason for failure (string)

        Note: Does not apply to UDP connections.
        """
        if self.__connected:
            return
        if self.Protocol == 'UDP':
            pass
        if self.__connected:
            return('ConnectedAlready')
        try:
            print('connecting to ip:{} port {}'.format(self.Hostname, self.IPPort))
            self.__socket = socket.create_connection((self.Hostname,self.IPPort))
        except Exception as e:
            print('failed to connect:{}'.format(str(e)))
            return('Connection Timeout')
        if self.__socket is not None:
            self.__connected = True
            if self.Protocol == 'TCP':
                self.__rec_thread_stop = False
                self.__rec_thread = threading.Thread(target=self.__recv_func(self.__socket))
                self.__rec_thread.start()
            if self.Connected is not None:
                self.Connected('Connected')
            return('Connected')
        elif self.Disconnected is not None:
            self.Disconnected('Disconnected')
            return('Disconnected')

    def Disconnect(self):
        """ Disconnect the socket

        Note: Does not apply to UDP connections.
        """
        if not self.__connected:
            return
        self.__rec_thread_stop = True
        self.__socket.shutdown(socket.SHUT_RDWR)
        self.__socket.close()
        self.__connected = False
        self.__socket = None
        if self.__socket is None:
            if self.Disconnected is not None:
                self.Disconnected('Disconnected')

    def Send(self, data:'str'):
        """ Send string over ethernet port if it's open

        Arguments:
            - data (bytes, string) - string to send out

        Raises:
            - TypeError
            - IOError
        """
        if not self.__connected:
            return
        try:
            if data:
                self.__socket.send(data.encode('utf-8'))
        except:
            pass

    def __recv_func(self,client:'socket.socket'):
        def r():
            while True:
                if self.__rec_thread_stop:
                    break
                try:
                    data = client.recv(4096)
                except:
                    if self.Disconnected is not None:
                        self.Disconnected('Disconnected')
                    self.Disconnect()
                    data = b''
                if self.ReceiveData is not None and len(data):
                    self.ReceiveData(self,data)
                time.sleep(0.001)
        return r

class IpcpLink():
    """
    node format:
    {
        'alias':{
            'node':obj,
            'ipcp':int,
            'type':str
        }
    }
    """
    nodes = {} #type:dict[str,dict[str,object]]
    ipcp_links = [] #type:list[IpcpLink]


    __default_password = 'p9oai23jr09p8fmvw98foweivmawthapw4t'


    def __get_alias_from_node(node):
        return node.alias

    def RegisterNode(node:ExtronNode):
        value = {'node':node,'ipcp':node._ipcp_index,'type':node._type}
        alias = node._alias
        IpcpLink.nodes[alias] = value
        return alias

    def __init__(self,ip_address,port='LAN',password=None):
        self.index = len(IpcpLink.ipcp_links)
        IpcpLink.ipcp_links.append(self)
        self.ip_address = ip_address
        self.password = password
        if self.password is None:
            self.password = IpcpLink.__default_password
        self.port = {'LAN':11991,'AVLAN':11990}[port]

        self.__client = _EthernetClientSimple(self.ip_address,self.port,'TCP')
        self.__client.ReceiveData = self.__HandleRecieveFromClient
        self.__client.Connected = self.__OnConnected
        self.__client.Disconnected = self.__OnDisconnected

        self.__system_is_connected = False
        self.__devices_clientbuffer = ''
        self.__delim = '~!END!~\x0a'
        self.__rxmatchpattern = f'(.*)~~(.*){self.__delim}'
        self.__tx_queue = queue.Queue()
        self.__tx_timer = Timer(0.1,self.__f_tx_timer())
        self.__tx_timer.Stop()

        self.__client.Connect()
        def f(timer,count):
            #print('client connect check:{}'.format(self.__system_is_connected))
            if not self.__system_is_connected:
                self.__client.Connect()
            else:
                self.__client.Send(self.__delim)
        self.connection_enforcement = Timer(5,f)

        self.System = System(self.index)



    def __removesuffix(self,data:'str',end:'str'):
        try:
            return data[data.index(end)+len(end):]
        except:
            return data
    def __HandleRecieveFromClient(self,client,data:'bytes'):
        if _debug:print(f'message received:{data.decode()}')
        self.__devices_clientbuffer += data.decode()
        while self.__delim in self.__devices_clientbuffer:
            delim_pos = self.__devices_clientbuffer.index(self.__delim)
            temp_buf = self.__devices_clientbuffer[:delim_pos+len(self.__delim)]
            self.__devices_clientbuffer = self.__removesuffix(self.__devices_clientbuffer,self.__delim)
            matches = re.findall(self.__rxmatchpattern,temp_buf)
            for match in matches:
                alias = match[0]
                msg = None
                try:
                    msg = json.loads(match[1])
                except Exception as e:
                    print('Error decoding message in response for alias {}:{}'.format(alias,str(e)))
                if msg and alias in self.nodes:
                    nodeevent = None
                    msg_type = msg['type']
                    if msg_type == 'query':
                        nodeevent = threading.Thread(target=self.nodes[alias]['node']._QueryResponse,args=(msg,))
                    if msg_type == 'update':
                        nodeevent = threading.Thread(target=self.nodes[alias]['node']._UpdateResponse,args=(msg,))
                    if msg_type == 'init':
                        nodeevent = threading.Thread(target=self.nodes[alias]['node']._InitResponse,args=(msg,))
                    if msg_type == 'error':
                        nodeevent = threading.Thread(target=self.nodes[alias]['node']._ErrorResponse,args=(msg,))
                    if nodeevent:nodeevent.start()



    def __OnConnected(self,value):
        print('IpcpLink {} Connected'.format(self.index))
        self.__system_is_connected = True
        self.__tx_queue.empty()
        self.__tx_timer.Restart()
        self.__client.Send('{}{}'.format(self.password,self.__delim))

        #cycle nodes calling connected event
        for alias in self.nodes:
            if self.nodes[alias]['ipcp'] == self.index:
                self.nodes[alias]['node']._LinkStatusChanged('Connected')
                self.nodes[alias]['node']._Initialize()
    def __OnDisconnected(self,value):
        self.__system_is_connected = False
        print('IpcpLink {} Disconnected'.format(self.index))
        #cycle nodes calling disconnected event
        self.__tx_queue.empty()
        self.__tx_timer.Stop()
        for alias in self.nodes:
            if self.nodes[alias]['ipcp'] == self.index:
                self.nodes[alias]['node']._LinkStatusChanged('Disconnected')

    def __f_tx_timer(self):
        def f_ipcp_link_tx_timer(timer,count):
            if not self.__system_is_connected:
                self.__tx_queue.empty()
                return
            messages = []
            while not self.__tx_queue.empty():
                msg = self.__tx_queue.get()
                self.__client.Send(msg)
                if _debug:print('message sent:{}'.format(msg))
        return f_ipcp_link_tx_timer



    def Command(self,msg):
        self.Send(msg)


    def Query(self,msg):
        self.Send(msg)

    def Init(self,msg):
        self.Send(msg)

    def Send(self,msg):
        if not self.__system_is_connected:
            return
        msg = f'{msg}{self.__delim}'
        self.__client.Send(msg)
        if _debug:print('message sent:{}'.format(msg))
        #self.__tx_queue.put(f'{msg}{self.__delim}')









class System(ExtronNode):
    """ Class to send System using the configured mail settings. The confiured settings can be over ridden during instantiation.

    Note: default sender will be login username@unit-name or hostname@unit-name if there is no authentication. To override, call Sender()

    ---

    Arguments:
        - smtpServer (string) - ip address or hostname of SMTP server
        - port (int) - port number
        - username (string) - login username for SMTP authentication
        - password (string) - login password for SMTP authentication
        - sslEnabled (bool) - Enable (True) or Disable (False) SSL for the connection
    """

    _type='System'
    def __init__(self,ipcp_index=0):
        """ System class constructor.

        """
        self._args = []
        self._ipcp_index = ipcp_index
        self._alias = f'System'
        self._callback_properties = []
        self._properties_to_reformat = []
        self._query_properties_init = {}
        self._query_properties_always = {}
        super().__init__(self)
        self._initialize_values()
    def _initialize_values(self):
        self._query_properties_init_list = list(self._query_properties_init.keys())
    def __format_parsed_update_value(self,property,value):
        if property in self._properties_to_reformat:
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



    def GetUnverifiedContext(self) -> None:
        """ Python 3.4.3 changed the default behavior of the stdlib http clients. They will now verify that “the server presents a certificate which is signed by a
        CA in the platform trust store and whose hostname matches the hostname being requested by default”. This method returns an unverified context for use when
        a valid certificate is impossible.

        Returns:
            - context (ssl.SSLContext) - unverified context object compatible with stdlib http clients.

        Warning:
            This is a potential security risk. It should only be used when a secure solution is impossible. GetSSLContext should be used whenever possible.
        """
        import ssl
        context = ssl._create_unverified_context()
        return context






    def GetSSLContext(self,alias) -> None:
        """ this actually fakes it.  This will need to be dumped on the server, not the IPCP controller, in the SSL Certificates folder"""
        """ Retrieve a Certificate Authority certificate from the Security Store and use it to create an SSL context usable with standard Python http clients.

        Parameters:
            alias (string) - name of the CA certificate file.

        Returns:
            - context (ssl.SSLContext) - an SSL context object compatible with stdlib http clients.

        example:
            import urllib.request
            from extronlib.system import GetSSLContext

            context = GetSSLContext('yourcert')

            urllib.request.urlopen("https://www.example.com", context=context)
        """
        import ssl,os
        __cwd = '{}{}'.format(os.getcwd(),'//extronlib//engine//SSL Certificates//')
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.load_verify_locations(capath=f'{__cwd}{alias}')
        return context





    # ------ TIME METHODS --------
    def SetAutomaticTime(self,Server: str) -> None:
        """ Turn on NTP time synchronization using Server as the time source.

        Arguments:
            - Server (string) – the NTP server to synchronize with
        """
        self._Command('SetAutomaticTime',[Server])


    def SetManualTime(self,DateAndTime: datetime) -> None:
        """ Change the system time. This will turn off NTP synchronization if it is on.

        Arguments:
            - Server (string) – the NTP server to synchronize with
        """
        self._Command('SetManualTime',[base64.b64encode(pickle.dumps(DateAndTime)).decode('utf-8')])


    def GetCurrentTimezone(self) -> tuple:
        """ The returned namedtuple contains three pieces of string data: the time zone id, the time zone description, and MSid which contains a Microsoft-compatible time zone identifier

        Returns:
            - namedtuple (tuple) – the current time zone of the primary controller
        """
        try:
            val = pickle.loads(base64.b64decode(self._Query('GetCurrentTimezone',[])))
        except:
            val = None
        return val


    def GetTimezoneList(self) -> list:
        """ Each item in the returned list is a namedtuple that contains three pieces of string data: the time zone id, the time zone description, and MSid which contains a Microsoft-compatible time zone identifier.

        Returns:
            - listof namedtuples (list) – all time zones supported by the system
        """
        try:
            val = pickle.loads(base64.b64decode(self._Query('GetTimezoneList',[])))
        except:
            val = None
        return val



    def SetTimeZone(self,id) -> None:
        """ Change the system time zone. Time zone affects Daylight Saving Time behavior and is used to calculate time of day when NTP time synchronization is turned on.

        Arguments:
            - id (string) –  The new system time zone identifier. Use an item returned by GetTimezoneList to get the time zone id for this parameter.
        """
        self._Command('SetTimeZone',[id])




    # ------ NETWORK METHODS --------
    def WakeOnLan(self,macAddress: str, port=9) -> None:
        """ Wake-on-LAN is an computer networking standard that allows a computer to be awakened by a network message. The network message, ‘Magic Packet’, is sent out through UDP broadcast, port 9.

        Arguments:
            - macAddress (string) - Target device’s MAC address. The format is six groups of two hex digits, separated by hyphens ('01-23-45-67-ab-cd', e.g.).
            - (optional) port (int) - Port on which target device is listening.

        Note: Typical ports for WakeOnLan are 0, 7 and 9.
        """
        self._Command('WakeOnLan',[macAddress,port])

    def Ping(self,hostname='localhost', count=5) -> tuple:
        """ Ping a host and return the result in a tuple: (# of success ping, # of failure ping , avg time)

        Arguments:
            - (optional) hostname (string) - IP address to ping.
            - (optional) count (int) - how many times to ping.

        Returns
            - tuple (# of success, # of fail, avg time ) (int, int, float)
        """
        try:
            val = pickle.loads(base64.b64decode(self._Query('Ping',[hostname,count])))
        except:
            val = None
        return val


    # ------ OTHER METHODS --------
    def GetSystemUpTime(self) -> int:
        """ Returns system up time in seconds.

        Returns
            - system up time in seconds (int)
        """
        return self._Query('GetSystemUpTime',[])

    def ProgramLog(self,Entry: str, Severity='error') -> None:
        """ Write entry to program log file.

        Arguments:
            - Entry (string) - the message to enter into the log
            - (optional) Severity (string) - indicates the severity to the log viewer. ('info', 'warning', or 'error')
        """
        self._Command('ProgramLog',[Entry,Severity])

    def SaveProgramLog(self,path=None) -> None:
        """ Write program log to file.

        Arguments:
            - Entry (string) - the message to enter into the log
            - (optional) Severity (string) - indicates the severity to the log viewer. ('info', 'warning', or 'error')
        """
        from extronlib.system import File
        if path == None:
            path = 'ProgramLog {}.txt'.format(datetime.now().strftime('%Y-%m-%d %H%M%S'))
        log = self._Query('SaveProgramLog',[path])
        #write log to file
        if File.Exists(path):
            mode = 'w'
        else:
            mode = 'x'
        f = File(path,mode)
        if f:
            f.write(log)















