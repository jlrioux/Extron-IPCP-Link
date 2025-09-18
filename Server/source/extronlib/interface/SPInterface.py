from extronlib.engine.IpcpLink import ExtronNode
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from extronlib.device import SPDevice
_debug = False
import traceback
import base64
class SPInterface(ExtronNode):
    """ This class will provide a common interface for controlling and collecting data from AV components on Extron devices (extronlib.device) and Extron Secure Platform devices (SPDevice).

    Note:
        -

    ---

    Arguments:
        - Host (extronlib.device) - handle to Extron device class that instantiated this interface class

    ---

    Parameters:
        - Host - Returns (extronlib.device) - the host device

    ---

    Events:
        - Offline - (Event) Triggers when port goes offline. The callback takes two arguments. The first one is the extronlib.interface.SPInterface instance triggering the event and the second one is a string ('Offline').
        - Online - (Event) Triggers when port goes online. The callback takes two arguments. The first one is the extronlib.interface.SPInterface instance triggering the event and the second one is a string ('Online').
        - ReceiveData - (Event) Receive Data event handler used for asynchronous transactions. The callback takes two arguments. The first one is the SPInterface instance triggering the event and the second one is a bytes string.
    """
    _type='SPInterface'
    def __init__(self, Host: 'SPDevice',ipcp_index=0):
        """ SPInterface class constructor.

        Arguments:
            - Host (extronlib.device) - handle to Extron device class that instantiated this interface class
        """
        self.Offline = None
        self.Online = None
        self.Host = Host
        self.ReceiveData = None


        self._args = [Host.DeviceAlias]
        self._ipcp_index = ipcp_index
        self._alias = f'{Host.DeviceAlias}:SPI'
        self._callback_properties = {'Offline':None,
                                     'Online':None,
                                     'ReceiveData':None}
        self._properties_to_reformat = ['ReceiveData']
        self._query_properties_init = {}
        self._query_properties_always = {}
        super().__init__(self)
        self._initialize_values()
    def _initialize_values(self):
        self._query_properties_init_list = list(self._query_properties_init.keys())
    def __format_parsed_update_value(self,property,value):
        if property in self._properties_to_reformat:
            if property == 'ReceiveData':
                if type(value) == list:
                    value = value[0]
                value = base64.b64decode(value)
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

    def Send(self, data):
        """ Send string over serial port if it’s open

        Arguments:
            - data (bytes, string) - data to send

        Raises:
            - TypeError
            - IOError
        """
        if type(data) == str:
            data = data.encode()
        data = base64.b64encode(data).decode('utf-8')
        self._Command('Send',[data])



