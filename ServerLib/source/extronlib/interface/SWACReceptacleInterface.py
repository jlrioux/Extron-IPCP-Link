from extronlib.engine.IpcpLink import ExtronNode
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from extronlib.device import ProcessorDevice,SPDevice
_debug = False
import traceback

class SWACReceptacleInterface(ExtronNode):
    """ This class provides a common interface to a switched AC power receptacle on an Extron product (extronlib.device). The user can instantiate the class directly or create a subclass to add, remove, or alter behavior for different types of devices.

    ---

    Arguments:
        - Host (extronlib.device) - handle to Extron device class that instantiated this interface class
        - Port (string) - port name (e.g. 'SAC1')

    ---

    Parameters:
        - CurrentChanged - Returns (float) - instantaneous current draw in Amperes
        - Host - Returns (extronlib.device) - handle to Extron device class that instantiated this interface class
        - Port - Returns (string) - port name
        - State - Returns (string) - current state of receptacle ('On', 'Off')

    ---

    Events:
        - CurrentChanged - (Event) triggers when the current draw changes. The callback takes two arguments. The first one is the SWACReceptacleInterface instance triggering the event, and the second is the current.
        - Offline - (Event) Triggers when port goes offline. The callback takes two arguments. The first one is the extronlib.interface instance triggering the event and the second one is a string ('Offline').
        - Online - (Event) Triggers when port goes offline. The callback takes two arguments. The first one is the extronlib.interface instance triggering the event and the second one is a string ('Online').

    """

    _type='SWACReceptacleInterface'
    def __init__(self, Host: 'ProcessorDevice|SPDevice', Port,ipcp_index=0):
        """ SWACReceptacleInterface class constructor.

        Arguments:
            - Host (extronlib.device) - handle to Extron device class that instantiated this interface class
            - Port (string) - port name (e.g. 'SAC1')
        """
        self.Host = Host
        self.Port = Port
        self._Current = 0.0
        self.Offline = False
        self.Online = True
        self._State = ''
        self.StateChanged = None


        self._args = [Host.DeviceAlias,Port]
        self._ipcp_index = ipcp_index
        self._alias = f'{Host.DeviceAlias}:{Port}'
        self._callback_properties = {'Offline':None,
                                     'Online':None,
                                     'StateChanged':{'var':'_State','value index':1}}
        self._properties_to_reformat = []
        self._query_properties_init = {'State':[]}
        self._query_properties_always = {'Current':[]}
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
    def State(self):
        if 'State' in self._query_properties_init_list:
            self._query_properties_init_list.remove('State')
            self._State = self._Query('State',[])
        if 'State' not in self._query_properties_always:
            return self._State
        return self._Query('State',[])
    @property
    def Current(self):
        if 'Current' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Current')
            self._Current = self._Query('Current',[])
        if 'Current' not in self._query_properties_always:
            return self._Current
        return self._Query('Current',[])



    def SetState(self, State):
        """ Sets output state to be set ('On' or 1, 'Off' or 0)

        Arguments:
            - State (int, string) - output state to be set ('On' or 1, 'Off' or 0)
        """
        if State in [0,1]:
            State = {0:'Off',1:'On'}[State]
        self._State = State
        self._Command('SetState',[State])



    def Toggle(self):
        """ Changes the state of the receptacle to the logical opposite of the current state.
        """
        self._Command('Toggle',[])
        self._State = self._Query('State',[])



