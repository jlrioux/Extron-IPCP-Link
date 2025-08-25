
from extronlib.system import SaveProgramLog,ProgramLog,SetManualTime,SetAutomaticTime,SetTimeZone,GetSystemUpTime
from extronlib.system import GetTimezoneList,GetCurrentTimezone,Ping,WakeOnLan,Email,RestartSystem
import json
import base64
import pickle
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


        """
            CONTAINER TO HOLD VALUES OF PROPERTIES OF THE OBJECT
            - properties that do not always exist should have initial values set here then adjusted below
        """
        self.Commands = {}

        #once init is complete, send dump of current values to remote server
        #once init is complete, send dump of current values to remote server
        self.WrapperBasics.send_message(alias,json.dumps({'type':'init','value':None}))
        self.initialized = True


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
            if hasattr(self,data['property']):
                attr = getattr(self,data['property'])
                if callable(attr):
                    try:
                        attr(*data['args'])
                    except Exception as e:
                        msg='failed to run property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e))
                        print(msg)
                        err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':msg}}
                else:
                    try:
                        attr = data['args'][0]
                    except Exception as e:
                        msg='failed to set property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e))
                        print(msg)
                        err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':msg}}
            else:
                err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':'property does not exist'}}
        elif data['type'] == 'query':
            if hasattr(self,data['property']):
                attr = getattr(self,data['property'])
                value = None
                if callable(attr):
                    try:
                        value = getattr(self,data['property'])(*data['args'])
                        update = {'property':data['property'],'value':value,'qualifier':None}
                    except Exception as e:

                        msg='failed to run property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e))
                        print(msg)
                        err_msg = {'property':data['property'],'value':None,'qualifier':{'code':msg}}
                else:
                    try:
                        value = getattr(self,data['property'])
                        update = {'property':data['property'],'value':value,'qualifier':None}
                    except Exception as e:
                        msg='failed to get property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e))
                        err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':msg}}
            else:
                err_msg = {'property':data['property'],'value':None,'qualifier':{'code':'property does not exist'}}
        if err_msg:
            if 'query id' in data:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','query id':data['query id'],'message':err_msg}))
            else:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','message':err_msg}))
        if update:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'query','query id':data['query id'],'message':update}))


    '''
        SSL METHODS
    '''
    def GetUnverifiedContext(self):
        #cannot be pickled
        #context = GetUnverifiedContext()
        #pickled = pickle.dumps(context)
        return None
    def GetSSLContext(self,alias):
        #cannot be pickled
        #context = GetSSLContext(alias)
        #pickled = pickle.dumps(context)
        return None

    '''
        TIME METHODS
    '''
    def SetAutomaticTime(self,Server):
        SetAutomaticTime(Server)
    def SetManualTime(self,DateAndTime):
        SetManualTime(pickle.loads(base64.b64decode((DateAndTime))))
    def GetCurrentTimezone(self):
        return base64.b64encode(pickle.dumps(GetCurrentTimezone())).decode('utf-8')
    def GetTimezoneList(self):
        return base64.b64encode(pickle.dumps(GetTimezoneList())).decode('utf-8')
    def SetTimeZone(self,id):
        SetTimeZone(id)

    '''
        NETWORK METHODS
    '''
    def Ping(self,hostname='localhost',count=5):
        item = Ping(hostname,count)
        return base64.b64encode(pickle.dumps(item)).decode('utf-8')
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
        return contents#base64.b64encode(pickle.dumps(contents)).decode('utf-8')
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