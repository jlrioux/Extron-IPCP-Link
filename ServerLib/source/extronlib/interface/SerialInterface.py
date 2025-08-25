from extronlib.engine.IpcpLink import ExtronNode
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from extronlib.device import ProcessorDevice,eBUSDevice,SPDevice
_debug = False
import traceback
import base64

class SerialInterface(ExtronNode):
    """ This class provides an interface to a serial port. This class allows the user to send data over the serial port in a synchronous or asynchronous manner. This class is used for all ports capable of serial communication (e.g., Serial Ports, IR Serial Ports).

    Note:
        - In synchronous mode, the user will use SendAndWait() to wait for the response.
        - In asynchronous mode, the user will assign a handler function to ReceiveData to handle responses.
        - If an IR/Serial port is passed in and it has already been instantiated as an IRInterface, an exception will be raised.

    ---

    Arguments:
        - Host (extronlib.device) - handle to Extron device class that instantiated this interface class
        - Port (string) - port name (e.g.  'COM1', 'IRS1')
        - (optional) Baud (int) - baudrate
        - (optional) Data (int) - number of data bits
        - (optional) Parity (string) - 'None', 'Odd' or 'Even'
        - (optional) Stop (int) - number of stop bits
        - (optional) FlowControl (string) - 'HW', 'SW', or 'Off'
        - (optional) CharDelay (float) - time between each character sent to the connected device
        - (optional) Mode (string) - mode of the port, 'RS232', 'RS422' or 'RS485'

    ---

    Parameters:
        - Baud - Returns (int) - the baud rate
        - CharDelay - Returns (float) - inter-character delay
        - Data - Returns (int) - the number of data bits
        - FlowControl - Returns (string) - flow control
        - Host - Returns (extronlib.device) - the host device
        - Mode - Returns (string) - the current Mode
        - Parity - Returns (string) - parity
        - Port - Returns (string) - the port name this interface is attached to
        - Stop - Returns (int) - number of stop bits

    ---

    Events:
        - Offline - (Event) Triggers when port goes offline. The callback takes two arguments. The first one is the extronlib.interface instance triggering the event and the second one is a string ('Offline').
        - Online - (Event) Triggers when port goes online. The callback takes two arguments. The first one is the extronlib.interface instance triggering the event and the second one is a string ('Online').
        - ReceiveData - (Event) Receive Data event handler used for asynchronous transactions. The callback takes two arguments. The first one is the SerialInterface instance triggering the event and the second one is a bytes string.
    """


    _type='SerialInterface'
    def __init__(self, Host: 'ProcessorDevice|eBUSDevice|SPDevice', Port, Baud=9600, Data=8, Parity='None', Stop=1, FlowControl='Off', CharDelay=0, Mode='RS232',ipcp_index=0):
        """ SerialInterface class constructor.

        Arguments:
            - Host (extronlib.device) - handle to Extron device class that instantiated this interface class
            - Port (string) - port name (e.g.  'COM1', 'IRS1')
            - (optional) Baud (int) - baudrate
            - (optional) Data (int) - number of data bits
            - (optional) Parity (string) - 'None', 'Odd' or 'Even'
            - (optional) Stop (int) - number of stop bits
            - (optional) FlowControl (string) - 'HW', 'SW', or 'Off'
            - (optional) CharDelay (float) - time between each character sent to the connected device
            - (optional) Mode (string) - mode of the port, 'RS232', 'RS422' or 'RS485'
        """
        self.Host = Host
        self.Port = Port
        self._Baud = Baud
        self._Data = Data
        self._Parity = Parity
        self._Stop = Stop
        self._FlowControl = FlowControl
        self._CharDelay = CharDelay
        self._Mode = Mode
        self.Offline = None
        self.Online = None
        self.ReceiveData = None


        self._args = [Host.DeviceAlias,Port,Baud,Data,Parity,Stop,FlowControl,CharDelay,Mode]
        self._ipcp_index = ipcp_index
        self._alias = f'{Host.DeviceAlias}:{Port}'
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
                value = [base64.b64decode(value[0])]
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
    def Baud(self):
        if 'Baud' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Baud')
            self._Baud = self._Query('Baud',[])
        if 'Baud' not in self._query_properties_always:
            return self._Baud
        return self._Query('Baud',[])
    @property
    def Data(self):
        if 'Data' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Data')
            self._Data = self._Query('Data',[])
        if 'Data' not in self._query_properties_always:
            return self._Data
        return self._Query('Data',[])
    @property
    def Parity(self):
        if 'Parity' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Parity')
            self._Parity = self._Query('Parity',[])
        if 'Parity' not in self._query_properties_always:
            return self._Parity
        return self._Query('Parity',[])
    @property
    def Stop(self):
        if 'Stop' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Stop')
            self._Stop = self._Query('Stop',[])
        if 'Stop' not in self._query_properties_always:
            return self._Stop
        return self._Query('Stop',[])
    @property
    def FlowControl(self):
        if 'FlowControl' in self._query_properties_init_list:
            self._query_properties_init_list.remove('FlowControl')
            self._FlowControl = self._Query('FlowControl',[])
        if 'FlowControl' not in self._query_properties_always:
            return self._FlowControl
        return self._Query('FlowControl',[])
    @property
    def CharDelay(self):
        if 'CharDelay' in self._query_properties_init_list:
            self._query_properties_init_list.remove('CharDelay')
            self._CharDelay = self._Query('CharDelay',[])
        if 'CharDelay' not in self._query_properties_always:
            return self._CharDelay
        return self._Query('CharDelay',[])
    @property
    def Mode(self):
        if 'Mode' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Mode')
            self._Mode = self._Query('Mode',[])
        if 'Mode' not in self._query_properties_always:
            return self._Mode
        return self._Query('Mode',[])










    def Initialize(self, Baud=None, Data=None, Parity=None, Stop=None, FlowControl=None, CharDelay=None, Mode=None):
        """ Initializes Serial Port to given values. User may provide any or all of the parameters. None leaves property unmodified.

        Arguments:
            - (optional) Baud (int) - baudrate
            - (optional) Data (int) - number of data bits
            - (optional) Parity (string) - 'None', 'Odd' or 'Even'
            - (optional) Stop (int) - number of stop bits
            - (optional) FlowControl (string) - 'HW', 'SW', or 'Off'
            - (optional) CharDelay (float) - time between each character sent to the connected device
            - (optional) Mode (string) - mode of the port, 'RS232', 'RS422' or 'RS485'
        """
        self._Baud = Baud
        self._Data = Data
        self._Parity = Parity
        self._Stop = Stop
        self._FlowControl = FlowControl
        self._CharDelay = CharDelay
        self._Mode = Mode
        self._Command('Initialize',[Baud,Data,Parity,Stop,FlowControl,CharDelay,Mode])

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


    def SendAndWait(self, data:'str', timeout:'float'=3, deliTag:'bytes'=None, deliRex:'str'=None,deliLen:'int'=None):
        """ Send data to the controlled device and wait (blocking) for response

        Note In addition to data and timeout, the method accepts an optional delimiter, which is used to compare against the received response. It supports any one of the following conditions:
            -    > deliLen (int) - length of the response
            -    > deliTag (byte) - suffix of the response
            -    > deliRex (regular expression object) - regular expression

        It returns after timeout seconds expires, or returns immediately if the optional condition is satisfied.

        Note: The function will return an empty byte array if timeout expires and nothing is received, or the condition (if provided) is not met.

        Arguments:
            - data (bytes, string) - data to send.
            - timeout (float) - amount of time to wait for response.
            - delimiter (see above) - optional conditions to look for in response.

        Returns
            - Response received data (may be empty) (bytes)
        """
        if type(data) == str:
            data = data.encode()
        data = base64.b64encode(data).decode('utf-8')
        if type(deliTag) == str:
            deliTag = deliTag.encode()
        if deliTag:
            deliTag = base64.b64encode(deliTag).decode('utf-8')
        res = self._Query('SendAndWait',[data,timeout,deliTag,deliRex,deliLen])
        if not res:return(b'')
        return base64.b64decode(res)





    def StartKeepAlive(self, interval, data):
        """ Repeatedly sends data at the given interval

        Arguments:
            - interval (float) - Time in seconds between transmissions
            - data (bytes) - data bytes to send
        """
        if type(data) == str:
            data = data.encode()
        data = base64.b64encode(data).decode('utf-8')
        self._Command('StartKeepAlive',[interval,data])


    def StopKeepAlive(self):
        """ Stop the currently running keep alive routine
        """
        self._Command('StopKeepAlive',[])



