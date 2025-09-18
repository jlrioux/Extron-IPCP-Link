from extronlib.engine.IpcpLink import ExtronNode
_debug = False
import traceback

class AdapterDevice(ExtronNode):
    def __str__(self):return(self.DeviceAlias)
    """
    This class provides a common interface to a TouchLink Control Adapter. The user can instantiate the class directly or create a subclass to add, remove, or alter behavior for different types of devices.

    Parameters:
    Host (UIDevice) – handle to Extron UIDevice to which the AdapterDevice is connected

    DeviceAlias (str) – The device alias of the Extron device.

    ---

    Properties:
        - DeviceAlias - Returns (`string`) - the device alias of the object
        - Host - Returns (extronlib.device.ProcessorDevice) - Handle to the Extron ProcessorDevice to which the AdapaterDevice is connected.
        - ModelName - Returns (`string`) - Model name of this device
        - PartNumber - Returns (`string`) - the part number of this device

    ---

    Events:
        - `Offline` - (Event) Triggers when the device goes offline. The callback takes two Parameters. The first one is the extronlib.device instance triggering the event and the second one is a string ('Offline').
        - `Online` - (Event) Triggers when the device comes online. The callback takes two Parameters. The first one is the extronlib.device instance triggering the event and the second one is a string ('Online').
    """



    _type='AdapterDevice'
    def __init__(self, Host: object, DeviceAlias: str,ipcp_index=0) -> None:
        """
        AdapterDevice class constructor.

        ---

        Parameters:
            - Host (`object`) - handle to Extron ProcessorDevice to which the AdapaterDevice is connected
            - DeviceAlias (`string`) - Device Alias of the Extron device
        """

        self.Offline = None
        """
        Event:
            - Triggers when the device goes offline.
            - The callback takes two arguments. The first one is the extronlib.device instance triggering the event and the second one is a string ('Offline').
        """
        self.Online = None
        """
        Event:
            - Triggers when the device comes online.
            - The callback takes two arguments. The first one is the extronlib.device instance triggering the event and the second one is a string ('Online').
        """
        self.DeviceAlias = DeviceAlias
        self.Host = Host
        """ Handle to the Extron ProcessorDevice to which the AdapterDevice is connected. """
        self._PartNumber = ''
        self._ModelName = ''


        self._args = [Host.DeviceAlias,DeviceAlias]
        self._ipcp_index = ipcp_index
        self._alias = f'{DeviceAlias}'
        self._callback_properties = {'Offline':None,
                                     'Online':None}
        self._properties_to_reformat = []
        self._query_properties_init = {'ModelName':[],
                                    'PartNumber':[]}
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
                    self._locks_values[msg_in['query id']] = None
                self.__OnError('{}:error on query attribute {}'.format(self._alias,property))
            elif 'qualifier' in msg:
                self.__OnError('{}:error on attribute {} with {}'.format(self._alias,property,msg['qualifier']))
            else:
                self.__OnError('{}:error on attribute {}'.format(self._alias,property))
        else:
            try:
                setattr(self,property,self.__format_parsed_update_value(property,value))
            except Exception as e:
                self.__OnError('Error setting {}.{} with exception: {}'.format(self._alias,property,traceback.format_exc()))
            if _debug:print('{}:set attribute {} to {}'.format(self._alias,property,value))
    def __OnError(self,msg):
        from datetime import datetime
        print(f'{datetime.now()}: {self._alias}: {msg}')


    @property
    def PartNumber(self):
        if 'PartNumber' in self._query_properties_init_list:
            self._query_properties_init_list.remove('PartNumber')
            self._PartNumber = self._Query('PartNumber',[])
        if 'PartNumber' not in self._query_properties_always:
            return self._PartNumber
        return self._Query('PartNumber',[])
    @property
    def ModelName(self):
        if 'ModelName' in self._query_properties_init_list:
            self._query_properties_init_list.remove('ModelName')
            self._ModelName = self._Query('ModelName',[])
        if 'ModelName' not in self._query_properties_always:
            return self._ModelName
        return self._Query('ModelName',[])








