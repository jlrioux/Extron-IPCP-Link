
from extronlib.device import ProcessorDevice as ObjectClass
from extronlib.system import Timer
import json
import base64

class ObjectWrapper(ObjectClass):
    def __str__(self):return(self.alias)
    type = 'ProcessorDevice'
    def __init__(self,p,alias,data):
        self.WrapperBasics = p
        self.alias = alias
        self.args = []
        for arg in data['args']:
            self.args.append(arg)
        self.args = data['args']
        self.initialized = False
        try:
            ObjectClass.__init__(self,*data['args']) #type:ObjectClass
        except Exception as e:
            print('failed to create {} "{}" with args "{}" with exception: {}'.format(ObjectWrapper.type,self.alias,self.args,str(e)))
            msg='failed to create {} "{}" with args "{}"\nwith exception: {}'.format(self.type,self.alias,data['args'],str(e))
            err_msg = {'property':'init','value':data['args'],'qualifier':{'code':msg}}
            self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','message':err_msg}))
            self.WrapperBasics.log_error('remotelib error:{}:{}'.format(self.alias,json.dumps(err_msg)))
            return


        """
            WRAPPER CONFIGURATION
        """
        event_attrs = ['Online','Offline','ExecutiveModeChanged','CurrentLoadChanged','CombinedCurrentChanged','CombinedWattageChanged','CombinedLoadStateChanged']
        self.set_get_attrs = ['CurrentLoad','DeviceAlias','ExecutiveMode','FirmwareVersion','Hostname','IPAddress','LinkLicenses','MACAddress','ModelName','PartNumber','SerialNumber','SystemSettings','UserUsage']
        self.callable_attrs = {'Reboot':None,
                               'SetExecutiveMode':None}


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
                    value = getattr(self,data['property'])
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
