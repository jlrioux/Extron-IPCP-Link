
from extronlib.ui import Button as ObjectClass
import json
import base64

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from remotelib_qxi.device.UIDevice import ObjectWrapper as UIDevice




class ObjectWrapper():
    def __str__(self):return(self.alias)
    type = 'Button'
    def __init__(self,p,alias,data):
        self.WrapperBasics = p
        self.alias = alias
        self.args = []
        for arg in data['args']:
            self.args.append(arg)
        while len(self.args) < 4:
            self.args.append(None)
        self.initialized = False
        self.host_alias = data['args'][0]

        if self.host_alias not in self.WrapperBasics.wrapped_objects['aliases by type']:
            self.host = None #type:UIDevice
            host_type = 'UIDevice'
        else:
            host_type = self.WrapperBasics.wrapped_objects['aliases by type'][self.host_alias]
            self.host = self.WrapperBasics.wrapped_objects[host_type][self.host_alias] #type:UIDevice
        data['args'][0] = self.host

        self.obj = None
        self.allow_make_obj = True
        if self.host.where_used_present:
            if not int(self.args[1]) in self.host.where_used_items['Button']:
                self.allow_make_obj = False

        if self.allow_make_obj and self.args:
            try:
                self.obj = ObjectClass(*data['args']) #type:ObjectClass
            except Exception as e:
                print('failed to create {} "{}" with args "{}" with exception: {}'.format(ObjectWrapper.type,self.alias,self.args,str(e)))
                msg='failed to create {} "{}" with args "{}"\nwith exception: {}'.format(self.type,self.alias,self.args,str(e))
                err_msg = {'property':'init','value':self.args,'qualifier':{'code':msg}}
                self.WrapperBasics.send_message(alias,json.dumps({'type':'init','value':None}))
                self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','message':err_msg}))
                return
        else:
            self.WrapperBasics.send_message(alias,json.dumps({'type':'init','value':None}))
            self.initialized = True
            self.WrapperBasics.register(self.type,self.alias,self)
            return

        """
            WRAPPER CONFIGURATION
        """
        self.event_attrs = ['Pressed','Released','Repeated','Tapped','Held']


        """
            Each event should be defined here and send an update to the remote server with the new value
        """
        for item in self.event_attrs:
            setattr(self.obj,item,self.create_event_handler(item))

        #once init is complete, send dump of current values to remote server
        if True:#host_type != 'UIDevice':
            self.send_init_values()
        self.initialized = True
        self.WrapperBasics.register(self.type,self.alias,self)

    def send_init_values(self):
        data = {}
        if self.allow_make_obj:
            data['Name'] = self.obj.Name
            data['Visible'] = self.obj.Visible
            data['Enabled'] = self.obj.Enabled
            data['State'] = self.obj.State
            data['PressedState'] = self.obj.PressedState
            data['BlinkState'] = self.obj.BlinkState
        self.WrapperBasics.send_message(self.alias,json.dumps({'type':'init','value':data}))

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
        err_msg = None
        update = None
        if data['type'] == 'init':
            if self.allow_make_obj:
                needs_redefined = False
                cur_arg = 0
                for arg in self.args:
                    if str(arg) != str(data['args'][cur_arg]):
                        needs_redefined=True
                        self.args[cur_arg] = data['args'][cur_arg]
                    cur_arg+=1
                if needs_redefined:
                    data['args'][0] = self.host
                    self.obj = ObjectClass(*data['args'])
                    for item in self.event_attrs:
                        setattr(self.obj,item,self.create_event_handler(item))
            self.send_init_values()
            return
        elif not self.initialized:
            err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':'object does not exist'}}
        elif data['type'] == 'command':
            if self.allow_make_obj:
                if hasattr(self.obj,data['property']):
                    attr = getattr(self.obj,data['property'])
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
            if self.allow_make_obj:
                if hasattr(self.obj,data['property']):
                    attr = getattr(self.obj,data['property'])
                    value = None
                    if callable(attr):
                        try:
                            value = attr(*data['args'])
                            update = {'property':data['property'],'value':value,'qualifier':None}
                        except Exception as e:
                            print('failed to run property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e)))
                    else:
                        try:
                            value = attr
                            update = {'property':data['property'],'value':value,'qualifier':None}
                        except Exception as e:
                            print('failed to get property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e)))
                            err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':'failed to set property'}}
                else:
                    err_msg = {'property':data['property'],'value':None,'qualifier':{'code':'property does not exist'}}
            else:
                err_msg = {'property':data['property'],'value':None,'qualifier':{'code':'object does not exist'}}
        if err_msg:
            if 'query id' in data:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','query id':data['query id'],'message':err_msg}))
            else:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','message':err_msg}))
        if update:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'query','query id':data['query id'],'message':update}))
