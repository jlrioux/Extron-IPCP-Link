from extronlib.engine.IpcpLink import ExtronNode
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from extronlib.device import ProcessorDevice
_debug = False
import traceback

class VolumeInterface(ExtronNode):
    """ This class will provide a common interface for controlling and collecting data from Volume Ports on Extron devices (extronlib.device). The user can instantiate the class directly or create a subclass to add, remove, or alter behavior for different types of devices.

    ---

    Arguments:
        - Host (extronlib.device) - handle to Extron device class that instantiated this interface class
        - Port (string) - port name (e.g. 'VOL1')

    ---

    Parameters:
        - Host - Returns (extronlib.device) - 	the host device
        - Level - Returns (int) - Current volume level (percentage).
        - Max - Returns (float) - Maximum level (0.0 V < Max <= 10.0 V).
        - Min - Returns (float) - Minimum level (0.0 V <= Min < 10.0 V).
        - Mute - Returns (string) - Current state of volume port mute. ('On', 'Off')
        - Port - Returns (string) - the port name this interface is attached to
        - SoftStart - Returns (string) - Current state of Soft Start. ('Enabled', 'Disabled')
    """


    _type='VolumeInterface'
    def __init__(self, Host: 'ProcessorDevice', Port,ipcp_index=0):
        """ VolumeInterface class constructor.

        Arguments:
            - Host (extronlib.device) - handle to Extron device class that instantiated this interface class
            - Port (string) - port name (e.g. 'VOL1')
        """
        self.Host = Host
        self.Port = Port
        self._Level = 0
        self._Max = 0.0
        self._Min = 0.0
        self._SoftStart = ''
        self._Mute = ''
        self.Offline = None
        self.Online = None


        self._args = [Host.DeviceAlias,Port]
        self._ipcp_index = ipcp_index
        self._alias = f'{Host.DeviceAlias}:{Port}'
        self._callback_properties = {'Offline':None,
                                     'Online':None}
        self._properties_to_reformat = []
        self._query_properties_init = {'Level':[],
                                    'Max':[],
                                    'Min':[],
                                    'SoftStart':[],
                                    'Mute':[]}
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



    @property
    def Level(self):
        if 'Level' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Level')
            self._Level = self._Query('Level',[])
        if 'Level' not in self._query_properties_always:
            return self._Level
        return self._Query('Level',[])
    @property
    def Max(self):
        if 'Max' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Max')
            self._Max = self._Query('Max',[])
        if 'Max' not in self._query_properties_always:
            return self._Max
        return self._Query('Max',[])
    @property
    def Min(self):
        if 'Min' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Min')
            self._Min = self._Query('Min',[])
        if 'Min' not in self._query_properties_always:
            return self._Min
        return self._Query('Min',[])
    @property
    def Mute(self):
        if 'Mute' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Mute')
            self._Mute = self._Query('Mute',[])
        if 'Mute' not in self._query_properties_always:
            return self._Mute
        return self._Query('Mute',[])
    @property
    def SoftStart(self):
        if 'SoftStart' in self._query_properties_init_list:
            self._query_properties_init_list.remove('SoftStart')
            self._SoftStart = self._Query('SoftStart',[])
        if 'SoftStart' not in self._query_properties_always:
            return self._SoftStart
        return self._Query('SoftStart',[])



    def SetLevel(self, Level):
        """ Sets Level of volume control port

        Arguments:
            - Level (int) - Level (0 % <= Value <= 100 %).
        """
        if self.Min <= Level <= self.Max:
            self._Level = Level
            self._Command('SetLevel',[Level])
        else:
            self.__OnError('SetLevel: Level out of range')

    def SetMute(self, Mute):
        """ Sets the mute state.

        Arguments:
            - Mute (string) - mute state ('On', 'Off').
        """
        if Mute in ['On','Off']:
            self._Mute = Mute
            self._Command('SetMute',[Mute])
        else:
            self.__OnError('SetMute: invalid mute state')

    def SetRange(self, Min, Max):
        """ Set volume control object’s range.

        Arguments:
            - Min (float) - minimum voltage
            - Max (float) - maximum voltage
        """
        self._Min = Min
        self._Max = Max
        self._Command('SetRange',[Min,Max])
        self._Level = self._Query('Level',[])



    def SetSoftStart(self, SoftStart):
        """ Enable or Disable Soft Start.

        Arguments:
            - SoftStart (string) - Soft Start state ('Enabled', 'Disabled').
        """
        if SoftStart in ['Enabled','Disabled']:
            self._SoftStart = SoftStart
            self._Command('SetSoftStart',[SoftStart])
        else:
            self.__OnError('SetSoftStart: invalid SoftStart state')


