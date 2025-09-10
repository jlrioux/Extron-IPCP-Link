
from extronlib.system import SaveProgramLog,ProgramLog,SetManualTime,SetAutomaticTime,SetTimeZone,GetSystemUpTime
from extronlib.system import GetTimezoneList,GetCurrentTimezone,Ping,WakeOnLan,Email,RestartSystem
import json
import base64

class ObjectWrapper():
    type = 'System'
    def __init__(self,p,alias,data):
        self.WrapperBasics = p
        self.alias = alias
        self.args = []
        for arg in data['args']:
            self.args.append(arg)
        self.args = data['args']
        self.initialized = False

        """
            WRAPPER CONFIGURATION
        """
        event_attrs = []
        self.set_get_attrs = []
        self.callable_attrs = {'GetUnverifiedContext':None,
                                 'GetSSLContext':None,
                                 'SetAutomaticTime':None,
                                 'SetManualTime':None,
                                 'GetCurrentTimezone':None,
                                 'GetTimezoneList':None,
                                 'SetTimeZone':None,
                                 'Ping':None,
                                 'WakeOnLan':None,
                                 'GetSystemUpTime':None,
                                 'ProgramLog':None,
                                 'SaveProgramLog':None,
                                 'RestartSystem':None,
                                 'SendEmail':None}

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


    def create_event_handler(self,property):
        def e(interface,*args):
            if property == 'ReceiveData':
                if type(args[0]) is str:
                    args[0] = args[0].encode()
                args[0] = base64.b64encode(args[0]).decode('utf-8')
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


    '''
        SSL METHODS
    '''
    def GetUnverifiedContext(self):
        return None
    def GetSSLContext(self,alias):
        return None

    '''
        TIME METHODS
    '''
    def SetAutomaticTime(self,Server):
        SetAutomaticTime(Server)
    def SetManualTime(self,DateAndTime):
        from datetime import datetime
        DateAndTime = datetime.strptime(DateAndTime,'%Y-%m-%d %H:%M:%S')
        SetManualTime(DateAndTime)
    def GetCurrentTimezone(self):
        val = GetCurrentTimezone()
        d = {'id':val.id,'description':val.description,'MSid':val.MSid}
        return d
    def GetTimezoneList(self):
        vals = GetTimezoneList()
        items = []
        for val in vals:
            items.append({'id':val.id,'description':val.description,'MSid':val.MSid})
        return items
    def SetTimeZone(self,id):
        SetTimeZone(id)

    '''
        NETWORK METHODS
    '''
    def Ping(self,hostname='localhost',count=5):
        vals = Ping(hostname,count)
        items = list(vals)
        return items
    def WakeOnLan(self,macAddress, port=9):
        WakeOnLan(macAddress,port)

    '''
        OTHER METHODS
    '''
    def GetSystemUpTime(self):
        return GetSystemUpTime()
    def ProgramLog(self,Entry, Severity='error'):
        ProgramLog(Entry, Severity)
    def SaveProgramLog(self,path=None):
        SaveProgramLog(path)
        from extronlib.system import File
        #open the file just written
        contents = None
        with File(path) as f:
            contents = f.read()
        return contents
    def RestartSystem(self):
        RestartSystem()


    '''
        EMAIL METHODS
    '''
    def SendEmail(self,data):
        mail = Email(
        smtpServer=data['smtpServer'],
        port=data['port'],
        username=data['username'],
        password=data['password'],
        sslEnabled=data['sslEnabled']
        )

        mail.Sender(data['sender'])

        mail.Receiver(data['receiver'])
        if data['receivercc']:
            mail.Receiver(data['receivercc'], cc=True)

        mail.Subject(data['subject'])

        mail.SendMessage(data['sendmessage'])