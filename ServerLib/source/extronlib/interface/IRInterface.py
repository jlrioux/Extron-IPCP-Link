from extronlib.engine.IpcpLink import ExtronNode
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from extronlib.device import ProcessorDevice,eBUSDevice,SPDevice
_debug = False
import traceback

class IRInterface(ExtronNode):
    """ This class provides an interface to an IR port. This class allows the user to transmit IR data through an IR or IR/Serial port.

    Note: If an IR/Serial port is passed in and it has already been instantiated as an SerialInterface, an exception will be raised.

    ---

    Arguments:
        - Host (extronlib.device) - handle to Extron device class that instantiated this interface class
        - Port (string) - port name (e.g., 'IRS1')
        - File (string) - IR file name (e.g. 'someDevice.eir')

    ---

    Parameters:
        - File - Returns (string) - file name
        - Host - Returns (extronlib.device) - handle to Extron device class that instantiated this interface class
        - Port - Returns (string) - port name

    ---

    Events:
        - Offline - (Event) Triggers when port goes offline. The callback takes two arguments. The first one is the extronlib.interface instance triggering the event and the second one is a string ('Offline').
        - Online - (Event) Triggers when port goes offline. The callback takes two arguments. The first one is the extronlib.interface instance triggering the event and the second one is a string ('Online').
    """



    _type='IRInterface'
    def __init__(self, Host: 'ProcessorDevice|eBUSDevice|SPDevice', Port, File,ipcp_index=0):
        """ IRInterface class constructor.

        Arguments:
            - Host (extronlib.device) - handle to Extron device class that instantiated this interface class
            - Port (string) - port name (e.g., 'IRS1')
            - File (string) - IR file name (e.g. 'someDevice.eir')
        """

        self.Host = Host
        self.Port = Port
        self.File = File
        self.Offline = None
        self.Online = None


        self._args = [Host.DeviceAlias,Port,File]
        self._ipcp_index = ipcp_index
        self._alias = f'{Host.DeviceAlias}:{Port}'
        self._callback_properties = {'Offline':None,
                                     'Online':None,
                                     'AnalogVoltageChanged':{'var':'_AnalogVoltage','value index':1},
                                     'StateChanged':{'var':'_State','value index':1}}
        self._properties_to_reformat = []
        self._query_properties_init = {'Mode':[],
                                    'Pullup':[],
                                    'Upper':[],
                                    'Lower':[],}
        self._query_properties_always = {'State':[],
                                    'AnalogVoltage':[]}
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

    def Initialize(self, File=None):
        """ Initializes IR Port to given file. None leaves property unmodified.

        Arguments:
            - (optional) File (string) - IR file name (e.g. 'someDevice.eir')
        """
        self.File = File
        self._Command('Initialize',[File])


    def PlayContinuous(self, irFunction):
        """ Begin playback of an IR function. Function will play continuously until stopped. Will complete at least one header, one body, and the current body.

        Arguments:
            - irFunction (string) - function within the driver to play

        Note: PlayContinuous is interruptable by subsequent Play function calls (PlayCount(), PlayTime()) and Stop().
        """
        self._Command('PlayContinuous',[irFunction])




    def PlayCount(self, irFunction, repeatCount=None):
        """  Play an IR function Count times. Function will play the header once and the body 1 + the specified number of repeat times.

        Arguments:
            - irFunction (string) - function within the driver to play
            - (optional) repeatCount  (int) - number of times to repeat the body (0-15)

        Note:
            - PlayCount is uninterruptible, except by Stop().
            - repeatCount of None means play the number defined in the driver.
        """
        self._Command('PlayCount',[irFunction,repeatCount])



    def PlayTime(self, irFunction, duration):
        """ Play an IR function for the specified length of time. Function will play the header once and the body as many times as it can. Playback will stop when the time runs out. Current body will be completed.

        Arguments:
            - irFunction (string) - function within the driver to play
            - duration (float) - time in seconds to play the function

       Note: PlayTime is uninterruptible, except by Stop().
        """
        self._Command('PlayTime',[irFunction,duration])



    def Stop(self):
        """ Stop the current playback. Will complete the current body.
        """
        self._Command('Stop',[])


