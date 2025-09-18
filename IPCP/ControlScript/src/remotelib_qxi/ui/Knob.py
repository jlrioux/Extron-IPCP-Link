
from extronlib.ui import Knob as ObjectClass
from extronlib.system import Timer
import json
import base64
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from remotelib_qxi.device.UIDevice import ObjectWrapper as UIDevice

class ObjectWrapper():
    def __str__(self):return(self.alias)
    type = 'Knob'
    def __init__(self,p,alias,data):
        self.WrapperBasics = p
        self.alias = alias
        self.args = []
        for arg in data['args']:
            self.args.append(arg)
        self.args = data['args']
        self.initialized = False
        self.host_alias = data['args'][0]


        """
            WRAPPER CONFIGURATION
        """
        self.event_attrs = ['Turned']
        self.set_get_attrs = ['Host','ID']
        self.callable_attrs = {}



        if self.host_alias not in self.WrapperBasics.wrapped_objects['aliases by type']:
            self.host = None #type:UIDevice
            host_type = 'UIDevice'
        else:
            host_type = self.WrapperBasics.wrapped_objects['aliases by type'][self.host_alias]
            self.host = self.WrapperBasics.wrapped_objects[host_type][self.host_alias]
        data['args'][0] = self.host

        self.obj = None
        if self.determine_object_presence() and self.args:
            try:
                self.obj = ObjectClass(*data['args']) #type:ObjectClass
            except Exception as e:
                print('failed to create {} "{}" with args "{}" with exception: {}'.format(ObjectWrapper.type,self.alias,self.args,str(e)))
                msg='failed to create {} "{}" with args "{}"\nwith exception: {}'.format(self.type,self.alias,self.args,str(e))
                err_msg = {'property':'init','value':self.args,'qualifier':{'code':msg}}
                self.WrapperBasics.send_message(alias,json.dumps({'type':'init','value':None}))
                self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','message':err_msg}))
                self.WrapperBasics.log_error('remotelib error:{}:{}'.format(self.alias,json.dumps(err_msg)))
                return
        else:
            self.WrapperBasics.send_message(alias,json.dumps({'type':'init','value':None}))
            self.initialized = True
            self.WrapperBasics.register(self.type,self.alias,self)
            return



        """
            Each event should be defined here and send an update to the remote server with the new value
        """
        for item in self.event_attrs:
            setattr(self.obj,item,self.create_event_handler(item))

        #once init is complete, send dump of current values to remote server
        if True:#host_type != 'UIDevice':
            self.WrapperBasics.send_message(alias,json.dumps({'type':'init','value':None}))
        self.initialized = True
        self.WrapperBasics.register(self.type,self.alias,self)

    def determine_object_presence(self):
        if self.host.where_used_present:
            if not int(self.args[1]) in self.host.where_used_items['Knob']:
                return False
        return True



    def create_event_handler(self,property):
        def e(interface,*args):
            update = {'property':property,'value':args,'qualifier':None}
            self.WrapperBasics.send_message(self.alias,json.dumps({'type':'update','message':update}))
        return e

    def receive_message(self,data:'dict'):
        err_msg = None
        update = None
        if data['type'] == 'init':
            if self.determine_object_presence():
                needs_redefined = False
                cur_arg = 0
                for arg in self.args:
                    if str(arg) != str(data['args'][cur_arg]):
                        needs_redefined=True
                        self.args[cur_arg] = data['args'][cur_arg]
                    cur_arg+=1
                if needs_redefined or not self.obj:
                    data['args'][0] = self.host
                    self.obj = ObjectClass(*data['args'])
                    for item in self.event_attrs:
                        setattr(self.obj,item,self.create_event_handler(item))
            self.send_init_values()
            return
        elif not self.initialized:
            err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':'object does not exist'}}
        elif data['type'] == 'command':
            if self.obj:
                if data['property'] in self.callable_attrs:
                    try:
                        self.callable_attrs[data['property']](*data['args'])
                    except Exception as e:
                        msg='failed to run property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e))
                        err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':msg}}
                elif data['property'] in self.set_get_attrs:
                    try:
                        setattr(self.obj,data['property'],data['args'][0])
                    except Exception as e:
                        msg='failed to set property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e))
                        err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':msg}}
                else:
                    err_msg = {'property':data['property'],'value':None,'qualifier':{'code':'property does not exist'}}
            else:
                err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':'property does not exist'}}
        elif data['type'] == 'query':
            if self.obj:
                if data['property'] in self.callable_attrs:
                    try:
                        value = self.callable_attrs[data['property']](*data['args'])
                        update = {'property':data['property'],'value':value,'qualifier':None}
                    except Exception as e:
                        msg='failed to run property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e))
                        err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':msg}}
                elif data['property'] in self.set_get_attrs:
                    try:
                        value = getattr(self.obj,data['property'],data['args'][0])
                        update = {'property':data['property'],'value':value,'qualifier':None}
                    except Exception as e:
                        msg='failed to set property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e))
                        err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':msg}}
                else:
                    err_msg = {'property':data['property'],'value':None,'qualifier':{'code':'property does not exist'}}
            else:
                err_msg = {'property':data['property'],'value':None,'qualifier':{'code':'object does not exist'}}
        if err_msg:
            if 'query id' in data:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','query id':data['query id'],'message':err_msg}))
            else:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','message':err_msg}))
            self.WrapperBasics.log_error('remotelib error:{}:{}'.format(self.alias,json.dumps(err_msg)))
        if update:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'query','query id':data['query id'],'message':update}))
