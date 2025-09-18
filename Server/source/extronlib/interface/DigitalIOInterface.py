from extronlib.engine.IpcpLink import ExtronNode
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from extronlib.device import ProcessorDevice,eBUSDevice,SPDevice
_debug = False
import traceback

class DigitalIOInterface(ExtronNode):
    """ This class will provide a common interface for controlling and collecting data from Digital IO ports on Extron devices (extronlib.device). The user can instantiate the class directly or create a subclass to add, remove, or alter behavior for different types of devices.

    ---

    Arguments:
        - Host (extronlib.device) - handle to Extron device class that instantiated this interface class
        - Port (string) - port name (e.g. 'DIO1')
        - (optional) Mode (string) - Possible modes are: 'DigitalInput' (default), and 'DigitalOutput'
        - (optional) Pullup (bool) - pull-up state on the port

    ---

    Parameters:
        - Host - Returns (extronlib.device) - handle to Extron device class that instantiated this interface class
        - Mode - Returns (string) - mode of the Digital IO port ('DigitalInput', 'DigitalOutput')
        - Port - Returns (string) - port name
        - Pullup - Returns (bool) - indicates if the Input port is being pulled up or not
        - State - Returns (string) - current state of Input port ('On', 'Off')

    ---

    Events:
        - Offline - (Event) Triggers when port goes offline. The callback takes two arguments. The first one is the extronlib.interface instance triggering the event and the second one is a string ('Offline').
        - Online - (Event) Triggers when port goes online. The callback takes two arguments. The first one is the extronlib.interface instance triggering the event and the second one is a string ('Online').
        - StateChanged - (Event) Triggers when the input state changes. The callback takes two arguments. The first one is the extronlib.interface instance triggering the event and the second one is a string ('On' or 'Off').
    """


    _type='DigitalIOInterface'
    def __init__(self, Host: 'ProcessorDevice|eBUSDevice|SPDevice', Port, Mode='DigitalInput', Pullup=False,ipcp_index=0):
        """ DigitalIOInterface class constructor.

        Arguments:
            - Host (extronlib.device) - handle to Extron device class that instantiated this interface class
            - Port (string) - port name (e.g. 'DIO1')
            - (optional) Mode (string) - Possible modes are: 'DigitalInput' (default), and 'DigitalOutput'
            - (optional) Pullup (bool) - pull-up state on the port
        """
        self.Host = Host
        self.Port = Port
        self._Mode = Mode
        self._Pullup = Pullup
        self.Offline = False
        self.Online = True
        self._State = ''
        self.StateChanged = None


        self._args = [Host.DeviceAlias,Port,Mode,Pullup]
        self._ipcp_index = ipcp_index
        self._alias = f'{Host.DeviceAlias}:{Port}'
        self._callback_properties = {'Offline':None,
                                     'Online':None,
                                     'StateChanged':{'var':'_State','value index':1}}
        self._properties_to_reformat = []
        self._query_properties_init = {'Mode':[],
                                    'Pullup':[]}
        self._query_properties_always = {'State':[]}
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
    def Mode(self):
        if 'Mode' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Mode')
            self._Mode = self._Query('Mode',[])
        if 'Mode' not in self._query_properties_always:
            return self._Mode
        return self._Query('Mode',[])
    @property
    def Pullup(self):
        if 'Pullup' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Pullup')
            self._Pullup = self._Query('Pullup',[])
        if 'Pullup' not in self._query_properties_always:
            return self._Pullup
        return self._Query('Pullup',[])

    def Initialize(self, Mode=None, Pullup=None):
        """ Initializes Digital IO Port to given values. User may provide any or all of theparameters. None leaves property unmodified.

        Arguments:
            - (optional) Mode (string) - Possible modes are: 'DigitalInput' (default), and 'DigitalOutput'
            - (optional) Pullup (bool) - pull-up state on the port
        """
        self._Mode = Mode
        self._Pullup = Pullup
        self._Command('Initialize',[Mode,Pullup])

    def Pulse(self, duration):
        """ Turns the port on for the specified time in seconds with 10ms accuracy and a 100ms minimum value.

        Arguments:
            - duration (float) - pulse duration
        """
        self._Command('Pulse',[duration])

    def SetState(self, State):
        """ Sets output state to be set ('On' or 1, 'Off' or 0)

        Arguments:
            - State (int, string) - output state to be set ('On' or 1, 'Off' or 0)
        """
        self._Command('SetState',[State])
        self._State = State

    def Toggle(self):
        """ Changes the state of the IO Object to the logical opposite of the current state.
        """
        self._Command('Toggle',[])
