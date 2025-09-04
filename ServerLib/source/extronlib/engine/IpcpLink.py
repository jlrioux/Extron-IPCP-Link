import re,json,threading,time,queue

_debug = False

class ExtronNode():
    def __init__(self,obj,send_ipcp_create=True,needs_sync=True):
        self._locks = {} #type:dict[str,threading.Lock]
        self._locks_lock = threading.Lock()
        self._locks_values = {}
        self.__query_id = 0
        self.ipcp_link = IpcpLink.ipcp_links[self._ipcp_index]
        IpcpLink.RegisterNode(self)
        self.LinkStatusCallback = None
        self.LinkStatus = 'Disconnected'
        if send_ipcp_create:
            self._Initialize(needs_sync=needs_sync)



    def __aquire_lock(self,key=None):
        while self._locks_lock.locked():
            time.sleep(0.001)
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
    def _BatchCommand(self,property,args):
        msg = f"{self._alias}~~{json.dumps({'type':'command','device type':self._type,'property':property,'args':args})}"
        self.ipcp_link.BatchCommand(msg)

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
    def _Initialize(self,needs_sync=True):
        msg = f"{self._alias}~~{json.dumps({'type':'init','device type':self._type,'args':self._args})}"
        self.ipcp_link.Init(msg)
        if needs_sync:
            key = self.__aquire_lock('init')
            while self._locks[key].locked():
                time.sleep(0.001)
            with self._locks_lock:
                del self._locks['init']
        #self._initialize_values()

    def _LinkStatusChanged(self,value):
        self.LinkStatus = value
        self._release_all_locks()
        if self.LinkStatusCallback:
                self.LinkStatusCallback(value)

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

        from extronlib.interface import EthernetClientInterface
        self.__client = EthernetClientInterface(self.ip_address,self.port,'TCP',thru_ipcp=False)
        self.__client_udp = EthernetClientInterface(self.ip_address,self.port+2,'UDP',thru_ipcp=False)
        self.__client.ReceiveData = self.__HandleRecieveFromClient()
        self.__client.Connected = self.__OnConnected()
        self.__client.Disconnected = self.__OnDisconnected()

        self.__system_is_connected = False
        self.__devices_clientbuffer = ''
        self.__delim = '~!END!~\x0a'
        self.__rxmatchpattern = f'(.*)~~(.*){self.__delim}'
        self.__tx_queue = queue.Queue()
        from extronlib.system import Timer
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

        self.batch_commands = ''

        from extronlib.system import System,RFile
        self.System = System(self.index)
        self.RFile = RFile(None,'r',None,None,self.index)



    def __removesuffix(self,data:'str',end:'str'):
        try:
            return data[data.index(end)+len(end):]
        except:
            return data
    def __HandleRecieveFromClient(self):
        def e(client,data:'bytes'):
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
                        print('Error decoding message in response for alias {}:{}:{}'.format(alias,str(e)),match[1])
                        continue
                    if msg and alias in self.nodes:
                        nodeevent = None
                        msg_type = msg['type']
                        if msg_type == 'query':
                            nodeevent = threading.Thread(target=self.nodes[alias]['node']._QueryResponse,args=(msg,))
                            #self.nodes[alias]['node']._QueryResponse(msg)
                        if msg_type == 'update':
                            nodeevent = threading.Thread(target=self.nodes[alias]['node']._UpdateResponse,args=(msg,))
                            #self.nodes[alias]['node']._UpdateResponse(msg)
                        if msg_type == 'init':
                            nodeevent = threading.Thread(target=self.nodes[alias]['node']._InitResponse,args=(msg,))
                            #self.nodes[alias]['node']._InitResponse(msg)
                        if msg_type == 'error':
                            nodeevent = threading.Thread(target=self.nodes[alias]['node']._ErrorResponse,args=(msg,))
                            #self.nodes[alias]['node']._ErrorResponse(msg)
                        if nodeevent:nodeevent.start()
        return e



    def __OnConnected(self):
        def e(interface,value):
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
        return e
    def __OnDisconnected(self):
        def e(interface,value):
            self.__system_is_connected = False
            print('IpcpLink {} Disconnected'.format(self.index))
            #cycle nodes calling disconnected event
            self.__tx_queue.empty()
            self.__tx_timer.Stop()
            for alias in self.nodes:
                if self.nodes[alias]['ipcp'] == self.index:
                    self.nodes[alias]['node']._LinkStatusChanged('Disconnected')
        return e
    def __f_tx_timer(self):
        def f_ipcp_link_tx_timer(timer,count):
            if not self.__system_is_connected:
                self.__tx_queue.empty()
                return
            messages = []
            while not self.__tx_queue.empty():
                messages.append('{}{}'.format(self.__tx_queue.get(),self.__delim))
                if len(messages) == 10:
                    msg = ''.join(messages)
                    self.__client.Send(msg)
                    messages = []
            msg = ''.join(messages)
            self.__client.Send(msg)
        return f_ipcp_link_tx_timer



    def Command(self,msg):
        self.Send(msg)

    def BatchCommand(self,msg):
        #self.__tx_queue.put(msg)
        #return
        msg = f'{msg}{self.__delim}'
        #self.__client_udp.Send(msg)
        self.__client.Send(msg)
        if _debug:print('message sent:{}'.format(msg))




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






















