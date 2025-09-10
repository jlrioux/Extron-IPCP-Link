
from extronlib.interface import EthernetClientInterface as ObjectClass
from extronlib.system import Timer,Wait,Ping
import json
import base64

class ObjectWrapper(ObjectClass):
    def __str__(self):return(self.alias)
    type = 'EthernetClientInterface'
    def __init__(self,p,alias,data):
        self.WrapperBasics = p
        self._server_ip = ''
        self._device_on_network = True
        self._test_ping_timer = Timer(5,self.__test_ping_loop())
        self._test_ping_timer.Stop()
        if self.WrapperBasics._ping_before_eci_connect in [None,True]:
            @Wait(1)
            def w():
                self.__test_ping()
        self.alias = alias
        self.args = []
        for arg in data['args']:
            if type(arg) is list:
                arg = tuple(arg)
            self.args.append(arg)
        self.initialized = False
        self.__is_connected = False

        if self.args:
            try:
                ObjectClass.__init__(self,*self.args) #type:ObjectClass
            except Exception as e:
                print('failed to create {} "{}" with args "{}" with exception: {}'.format(ObjectWrapper.type,self.alias,self.args,str(e)))
                msg='failed to create {} "{}" with args "{}"\nwith exception: {}'.format(self.type,self.alias,self.args,str(e))
                err_msg = {'property':'init','value':self.args,'qualifier':{'code':msg}}
                self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','message':err_msg}))
                self.WrapperBasics.log_error('remotelib error:{}:{}'.format(self.alias,json.dumps(err_msg)))
                return


        """
            WRAPPER CONFIGURATION
        """
        event_attrs = ['Connected','Disconnected','ReceiveData']
        self.set_get_attrs = ['Credentials','Hostname','IPAddress','IPPort','Protocol','ServicePort']
        self.callable_attrs = {'Connect':None,
                                 'Disconnect':None,
                                 'SSLWrap':None,
                                 'Send':self._Send,
                                 'SendAndWait':self._SendAndWait,
                                 'SetBufferSize':None,
                                 'StartKeepAlive':self._StartKeepAlive,
                                 'StopKeepAlive':None}


        """
            Each event should be defined here and send an update to the remote server with the new value
        """
        for item in event_attrs:
            setattr(self,item,self.create_event_handler(item))
        for attr in self.callable_attrs:
            if not self.callable_attrs[attr]:
                self.callable_attrs[attr] = getattr(self,attr)

        #once init is complete, send dump of current values to remote server
        self.WrapperBasics.send_message(alias,json.dumps({'type':'init','value':None}))
        self.initialized = True
        self.WrapperBasics.register(self.type,self.alias,self)


    def __test_ping(self):
        if self._server_ip:
            res = Ping(self._server_ip,1)
            #print('TestPing:{} result:{}'.format(self._server_ip,res))
            enable = res[0] > 0
            if enable:
                self._test_ping_timer.Restart()
    def __test_ping_loop(self):
        def t(timer,count):
            res = Ping(self.Hostname,1)
            #print('Ping:{} result:{}'.format(self.Hostname,res))
            self._device_on_network = res[0] > 0
        return t



    def create_event_handler(self,property):
        def e(interface,*args):
            if property == 'ReceiveData':
                args = list(args)
                if type(args[0]) is str:
                    args[0] = args[0].encode()
                args[0] = base64.b64encode(args[0]).decode('utf-8')
                args = tuple(args)
            if property == 'Connected':
                self.__is_connected = True
            elif property == 'Disconnected':
                self.__is_connected = False
            update = {'property':property,'value':args,'qualifier':None}
            self.WrapperBasics.send_message(self.alias,json.dumps({'type':'update','message':update}))
        return e

    def receive_message(self,data:'dict'):
        if not self.initialized:return
        err_msg = None
        update = None
        if data['type'] == 'init':
            self.WrapperBasics.send_message(self.alias,json.dumps({'type':'init','value':None}))
        elif data['type'] == 'command':
            if data['property'] in self.callable_attrs:
                try:
                    self.callable_attrs[data['property']](*data['args'])
                except Exception as e:
                    msg='failed to run property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e))
                    err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':msg}}
            elif data['property'] in self.set_get_attrs:
                try:
                    setattr(self,data['property'],data['args'][0])
                except Exception as e:
                    msg='failed to set property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e))
                    err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':msg}}
            else:
                err_msg = {'property':data['property'],'value':None,'qualifier':{'code':'property does not exist'}}
        elif data['type'] == 'query':
            if data['property'] in self.callable_attrs:
                try:
                    value = self.callable_attrs[data['property']](*data['args'])
                    update = {'property':data['property'],'value':value,'qualifier':None}
                except Exception as e:
                    msg='failed to run property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e))
                    err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':msg}}
            elif data['property'] in self.set_get_attrs:
                try:
                    value = getattr(self,data['property'],data['args'][0])
                    update = {'property':data['property'],'value':value,'qualifier':None}
                except Exception as e:
                    msg='failed to set property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e))
                    err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':msg}}
            else:
                err_msg = {'property':data['property'],'value':None,'qualifier':{'code':'property does not exist'}}
        if err_msg:
            if 'query id' in data:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','query id':data['query id'],'message':err_msg}))
            else:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','message':err_msg}))
            self.WrapperBasics.log_error('remotelib error:{}:{}'.format(self.alias,json.dumps(err_msg)))
        if update:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'query','query id':data['query id'],'message':update}))

    def _Connect(self,timeout=None):
        if not self._device_on_network:
            return 'No route to host'
        return self.Connect(timeout)
    def _SendAndWait(self,data:'str', timeout:'float'=3, deliTag:'bytes'=None, deliRex:'str'=None,deliLen:'int'=None):
        if not self._device_on_network:
            val = b''
        else:
            data = base64.b64decode(data)
            val = b''
            if deliTag:
                deliTag = base64.b64decode(deliTag)
                val = self.SendAndWait(data, timeout, deliTag=deliTag)
            elif deliRex:
                val = self.SendAndWait(data, timeout, deliRex=deliRex)
            elif deliLen:
                val = self.SendAndWait(data, timeout, deliLen=deliLen)
            if val == None:val = b''
        return base64.b64encode(val).decode('utf-8')

    def _Send(self,data:'str'):
        data = base64.b64decode(data)
        self.Send(data)

    def _StartKeepAlive(self, interval, data):
        data = base64.b64decode(data)
        self.StartKeepAlive(interval, data)