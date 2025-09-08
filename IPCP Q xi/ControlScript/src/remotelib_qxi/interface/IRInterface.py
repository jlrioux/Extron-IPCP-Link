
from extronlib.interface import IRInterface as ObjectClass
from extronlib.system import Timer
import json
import base64

class ObjectWrapper(ObjectClass):
    def __str__(self):return(self.alias)
    type = 'IRInterface'
    def __init__(self,p,alias,data):
        self.WrapperBasics = p
        self.alias = alias
        self.args = []
        for arg in data['args']:
            self.args.append(arg)
        self.args = data['args']
        self.initialized = False
        self.host_alias = data['args'][0]
        if self.host_alias not in self.WrapperBasics.wrapped_objects['aliases by type']:
            self.host = None
        else:
            host_type = self.WrapperBasics.wrapped_objects['aliases by type'][self.host_alias]
            self.host = self.WrapperBasics.wrapped_objects[host_type][self.host_alias]
        data['args'][0] = self.host
        try:
            ObjectClass.__init__(self,*data['args']) #type:ObjectClass
        except Exception as e:
            print('failed to create {} "{}" with args "{}" with exception: {}'.format(ObjectWrapper.type,self.alias,str(self.args),str(e)))
            msg='failed to create {} "{}" with args "{}"\nwith exception: {}'.format(ObjectWrapper.type,self.alias,str(self.args),str(e))
            err_msg = {'property':'init','value':str(self.args),'qualifier':{'code':msg}}
            self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','message':err_msg}))
            self.WrapperBasics.log_error('remotelib error:{}:{}'.format(self.alias,json.dumps(err_msg)))
            return


        """
            WRAPPER CONFIGURATION
        """
        event_attrs = ['Online','Offline']


        """
            Each event should be defined here and send an update to the remote server with the new value
        """
        for item in event_attrs:
            setattr(self,item,self.create_event_handler(item))

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
            self.WrapperBasics.log_error('remotelib error:{}:{}'.format(self.alias,json.dumps(err_msg)))
        if update:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'query','query id':data['query id'],'message':update}))