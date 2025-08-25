from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from extronlib.device import UIDevice
from extronlib.engine.IpcpLink import ExtronNode
_debug = False
import traceback

class Knob(ExtronNode):
    """ Knob is a rotary control that has 36 steps for a full revolution

    ---

    Arguments:
        - UIHost (extronlib.device.UIDevice) - Device object hosting this UIObject
        - ID (int) - ID of the UIObject

    ---

    Parameters:
        - Host - Returns (extronlib.device.UIDevice) - UIDevice object that hosts this control object
        - ID - Returns (int) - the object ID

    ---

    Events:
        - Turned - (Event) Get/Set callback when knob is turned. The callback takes two parameters. The first one is the Knob itself and the second one is a signed integer indicating steps that was turned. Positive values indicate clockwise rotation.
    """

    _type='Knob'
    def __init__(self, UIHost:'UIDevice', ID:'int',ipcp_index=0):
        """ Knob class constructor.

        Arguments:
            - UIHost (extronlib.device.UIDevice) - Device object hosting this UIObject
            - ID (int) - ID of the UIObject
        """
        self.UIHost = UIHost
        self.ID = ID
        self.Turned = None

        self._args = [UIDevice.DeviceAlias,ID]
        self._ipcp_index = ipcp_index
        self._alias = f'{UIDevice.DeviceAlias}:{ID}'
        self._callback_properties = {'Turned':None}
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

