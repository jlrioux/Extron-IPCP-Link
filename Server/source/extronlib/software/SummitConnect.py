from extronlib.engine.IpcpLink import ExtronNode
_debug = False
import traceback
import base64

class SummitConnect(ExtronNode):
    """ This class provides an interface to Extron Unified Communications solutions.

    Note:
        - System limits 15 SummitConnect clients per system.

    ---

    Arguments:
        - Hostname (string) - Hostname of the host computer. Can be IP Address.
        - IPPort (int) - IP Port the software is listening on (default is 5000)

    Note:
        - Only one object can be instantiated for a given Hostname or IP Address.

    ---

    Parameters:
        - Hostname - Returns (string) - Hostname of the host computer `Note: If unavailable, returns the IP Address.`
        - IPAddress - Returns (string) - IP Address of the host computer
        - IPPort - Returns (int) - IP Port the software is listening on (default is 5000)
        - ListeningPort - Returns (int) - IP Port this SummitConnect instance is listening on for received data

    ---

    Events:
        - Connected (Event) Triggers when communication is established. The callback takes two arguments. The first one is the SummitConnect instance triggering the event and the second one is a string ('Connected').
        - Disconnected (Event) Triggers when the communication is broken. The callback takes two arguments. The first one is the SummitConnect instance triggering the event and the second one is a string ('Disconnected').
        - ReceiveData (Event) Receive Data event handler used for asynchronous transactions. The callback takes two arguments. The first one is the SummitConnect instance triggering the event and the second one is a bytes string.

    ---

    Example:
    ```
    from extronlib.software import SummitConnect
    ConferencePC = SummitConnect('192.168.1.110')
    ```
    """

    _type='SummitConnect'
    def __init__(self, Hostname: str, IPPort: int=None,ipcp_index=0) -> None:
        """ SummitConnect class constructor.

        Arguments:
            - Hostname (string) - Hostname of the host computer. Can be IP Address.
            - IPPort (int) - IP Port the software is listening on (default is 5000)
        """
        self.Hostname = Hostname
        self.IPPort = IPPort
        self._IPAddress = None
        self._ListeningPort = None

        self.Connected = None
        self.Disconnected = None
        self.ReceiveData = None


        self._args = [Hostname,IPPort]
        self._ipcp_index = ipcp_index
        self._alias = f'SC:{Hostname}:{IPPort}'
        self._callback_properties = {'Connected':None,
                                     'Disconnected':None,
                                     'ReceiveData':None}
        self._properties_to_reformat = ['ReceiveData']
        self._query_properties_init = {}
        self._query_properties_always = {'IPAddress':[],
                                    'ListeningPort':[]}
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




    @property
    def IPAddress(self):
        if 'IPAddress' in self._query_properties_init_list:
            self._query_properties_init_list.remove('IPAddress')
            self._IPAddress = self._Query('IPAddress',[])
        if 'IPAddress' not in self._query_properties_always:
            return self._IPAddress
        return self._Query('IPAddress',[])
    @property
    def ListeningPort(self):
        if 'ListeningPort' in self._query_properties_init_list:
            self._query_properties_init_list.remove('ListeningPort')
            self._ListeningPort = self._Query('ListeningPort',[])
        if 'ListeningPort' not in self._query_properties_always:
            return self._ListeningPort
        return self._Query('IPAddress',[])




    def Connect(self, timeout: float=None) -> str:
        """ Connect to the software.

        Arguments:
            - timeout (float) - time in seconds to attempt connection before giving up.

        Returns
            - 'Connected' or reason for failure ('TimedOut', 'HostError', 'PortUnavailable:<port>, ...'). (string)

        ---

        Example:
        ```
        def ConnectToSoftware():
            -    result = ConferencePC.Connect(5)
            -    if result in ['TimedOut', 'HostError']:
            -        Wait(30, ConnectToSoftware)
            -    else:
            -        GetStatus(ConferencePC)    # GetStatus() is a user function

        ConnectToSoftware()
        ```
        """
        self._Query('Connect',[timeout])

    def Disconnect(self) -> None:
        """ Disconnect the socket

        >>> ConferencePC.Disconnect()
        """
        self._Command('Disconnect',[])

    def Send(self, data) -> None:
        """ Send string to licensed software

        Arguments:
            -    - data (bytes, string) - string to send out

        >>> ConferencePC.Send(A_MESSAGE)
        """
        if type(data) == str:
            data = data.encode()
        data = base64.b64encode(data).decode('utf-8')
        self._Command('Send',[data])

    def SetListeningPorts(self, portList: list=None) -> str:
        """ Set the ports to listen for received data.

        Arguments:
            - (optional) portList (list of ints) - list of ports (e.g. [10000, 10001, 10002]). None will set to default range.

        Returns:
            - 'Listening' or a reason for failure (e.g. 'PortUnavailable:<port>, ...')

        Note:
            -    - A maximum of 15 ports can be specified.
            -    - Default port range is 5001 - 5008

        ---

        Example:
        ```
        # Listen on ports 10000, 10001, and 10002
        SummitConnect.SetListeningPorts(range(10000, 10003))
        ...
        SummitConnect.SetListeningPorts()    # Reset to default.
        ```
        """
        return self._Query('SetListeningPorts',[portList])
