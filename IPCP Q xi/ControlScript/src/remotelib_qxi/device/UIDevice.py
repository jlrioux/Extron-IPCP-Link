
from extronlib.device import UIDevice as ObjectClass
from extronlib.system import Wait
import json
import base64
#from extronlib.ui import Button,Label,Level,Slider,Knob
from remotelib_qxi.ui.Button import ObjectWrapper as wButton
from remotelib_qxi.ui.Label import ObjectWrapper as wLabel
from remotelib_qxi.ui.Level import ObjectWrapper as wLevel
from remotelib_qxi.ui.Slider import ObjectWrapper as wSlider
from remotelib_qxi.ui.Knob import ObjectWrapper as wKnob


class ObjectWrapper(ObjectClass):
    def __str__(self):return(self.alias)
    type = 'UIDevice'
    def __init__(self,p,alias,data):
        self.WrapperBasics = p
        self.alias = alias
        self.args = []
        for arg in data['args']:
            self.args.append(arg)
        self.args = data['args']
        self.initialized = False
        if self.args:
            try:
                ObjectClass.__init__(self,*data['args']) #type:ObjectClass
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
        event_attrs = ['BrightnessChanged','HDCPStatusChanged','InactivityChanged','InputPresenceChanged','LidChanged','LightChanged','MotionDetected',
                       'Offline','Online','OverTemperatureChanged','OverTemperatureWarning','SleepChanged']
        self.set_get_attrs = ['AmbientLightValue','AutoBrightness','Brightness','DeviceAlias','DisplayState','DisplayTimer','DisplayTimerEnabled',
                              'FirmwareVersion','Hostname','IPAddress','InactivityTime','LidState','LightDetectedState','LinkLicenses','MACAddress',
                              'ModelName','MotionDecayTime','MotionState','OverTemperature','OverTemperatureWarningState','PartNumber','SerialNumber',
                              'SleepState','SleepTimer','SleepTimerEnabled','SystemSettings','UserUsage','WakeOnMotion']
        self.callable_attrs = {'Click':None,
                               'GetHDCPStatus':None,
                               'GetInputPresence':None,
                               'GetMute':None,
                               'GetVolume':None,
                               'HideAllPopups':None,
                               'HidePopupGroup':None,
                               'PlaySound':None,
                               'Reboot':None,
                               'SetAutoBrightness':None,
                               'SetBrightness':None,
                               'SetDisplayTimer':None,
                               'SetInactivityTime':None,
                               'SetInput':None,
                               'SetLEDBlinking':None,
                               'SetLEDState':None,
                               'SetMotionDecayTime':None,
                               'SetMute':None,
                               'SetSleepTimer':None,
                               'SetVolume':None,
                               'SetWakeOnMotion':None,
                               'ShowPopup':None,
                               'ShowPage':None,
                               'Sleep':None,
                               'StopSound':None,
                               'Wake':None}

        """
            Each event should be defined here and send an update to the remote server with the new value
        """
        for item in event_attrs:
            setattr(self,item,self.create_event_handler(item))
        for attr in self.callable_attrs:
            if not self.callable_attrs[attr]:
                self.callable_attrs[attr] = getattr(self,attr)

        #once init is complete, send dump of current values to remote server
        self.initialized = True
        self.WrapperBasics.register(self.type,self.alias,self)
        self.where_used_present = False
        self.where_used_items = {
            'Button':{},
            'Label':{},
            'Level':{},
            'Slider':{},
            'Knob':{}
        }
        self.item_constructors = {
            'Button':wButton,
            'Label':wLabel,
            'Level':wLevel,
            'Slider':wSlider,
            'Knob':wKnob
        }
        #@Wait(0.1)
        #def w():
        self.check_where_used()
        self.WrapperBasics.send_message(alias,json.dumps({'type':'init','value':None}))
    def check_where_used(self):
        from extronlib.system import RFile
        filename = '{}.csv'.format(self.DeviceAlias)
        if RFile.Exists(filename):
            self.where_used_present = True
            print('WhereUsed for panel "{}" found'.format(self.DeviceAlias))
            with RFile(filename) as f:
                for line in f:
                    parts = line.split(',')
                    if len(parts) == 5:
                        type = parts[1][1:-1]
                        if type in self.where_used_items:
                            id = int(parts[0][1:-1])
                            if id > 0 and id not in self.where_used_items[type]:
                                item_alias = '{}:{}'.format(self.alias,id)
                                data = {'args':[self.alias,id]}
                                self.where_used_items[type][id] = None
                                self.where_used_items[type][id] = self.item_constructors[type](self.WrapperBasics,item_alias,data)
            print('done processing WhereUsed for panel "{}" buttons:{} labels:{} levels:{} sliders:{} knobs:{}'.format(self.DeviceAlias,len(self.where_used_items['Button']),
                                                                                                                     len(self.where_used_items['Label']),
                                                                                                                     len(self.where_used_items['Level']),
                                                                                                                     len(self.where_used_items['Slider']),
                                                                                                                     len(self.where_used_items['Knob'])))


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
