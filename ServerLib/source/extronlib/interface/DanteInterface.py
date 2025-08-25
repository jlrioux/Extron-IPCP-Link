from extronlib.engine.IpcpLink import ExtronNode
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from extronlib.software.DanteDomainManager import DanteDomainManager
import base64
_debug = False
import traceback


class DanteInterface(ExtronNode):
    """ This class will provide a common interface for controlling and collecting data from Dante Input ports on Extron devices (extronlib.device). The user can instantiate the class directly or create a subclass to add, remove, or alter behavior for different types of devices.

    Parameters:
        - DeviceName (string) - Device name of the Dante controlled device.
        - Protocol (string) - Protocol type used. ('Extron' is the only supported protocol at this time)
        - DanteDomainManager (DanteDomainManager) - Dante Domain Manager of the Dante controlled device.
        - Domain (string) - Dante domain this device is assigned to.

    ---

    Events:
        - Disconnected - (Event) Triggers when a connection is broken
        - Connected - (Event) Connected
        - ReceiveData - (Event) Receive Data event handler used for asynchronous transactions
    """


    _type='DanteInterface'
    def __init__(self, DeviceName: str, Protocol='Extron',DanteDomainManager:'DanteDomainManager|None'=None,Domain=None,ipcp_index=0):
        """ DanteInterface class constructor.

        Arguments:
            - DeviceName (str) – Device name of the Dante controlled device.
            - Protocol (str) – Protocol type used. (‘Extron’ is the only supported protocol at this time)
            - DanteDomainManager (DanteDomainManager) – Dante Domain Manager of the Dante controlled device.
            - Domain (str) – Dante domain this device is assigned to.
        """
        self.DeviceName = DeviceName
        """ Device name of the Dante controlled device."""
        self.Protocol = Protocol
        """Protocol type used. (‘Extron’ is the only supported protocol at this time)"""
        self.DanteDomainManager = DanteDomainManager
        """Dante Domain Manager of the Dante controlled device."""
        self._Domain = Domain
        """Dante domain this device is assigned to."""

        """
        from extronlib import event, Version
        from extronlib.interface import DanteInterface

        print(Version())

        # Always required once per project
        DanteInterface.StartService('AVLAN')

        axi22at = DanteInterface('AXI22-AB-CD-EF')

        def ConnectAXI22at():
            result = axi22at.Connect(5)
            if 'Connected' not in result:
                Wait(30, ConnectAXI22at)
            else:
                GetStatus(axi22at)    # GetStatus() is a user function

        ConnectAXI22at()

        @event(axi22at, ['Connected', 'Disconnected'])
        def handleConnection(interface, state):
            print(interface.Hostname, state)

        @event(axi22at, 'ReceiveData')
        def handleRecvData(interface, data):
            print(interface.Hostname, data)
                ```
                @event(SomeInterface, ['Online', 'Offline'])
                def HandleConnection(interface, state):
                    print('{} is now {}'.format(interface.Port, state))
                ```
        """
        self.Connected = None
        """
        Event:
            -Triggers when a connection is established.
            -The callback takes two arguments. The first one is the DanteInterface instance triggering the event and the second one is a string ('Connected').
        """
        self.Disconnected = None
        """	Event:
                - Triggers when a connection is broken
                - The callback takes two arguments. The first one is the DanteInterface instance triggering the event and the second one is a string ('Disconnected').
        """
        self.ReceiveData = None

        """
        Event:
            - Receive Data event handler used for asynchronous transactions
            - The callback takes two arguments. The first one is the DanteInterface instance triggering the event and the second one is a bytes object.
            - Dante controlled devices always provide verbose, tagged responses.
            - The maximum amount of data per ReceiveData event that will be passed into the handler is 1024 bytes. For payloads greater than 1024 bytes, multiple events will be triggered.
        ```
        @event(axi22at, 'ReceiveData')
        def handleRecvData(interface, data):
            print(interface.Hostname, data)
        ```
        """

        self._args = [DeviceName, Protocol,DanteDomainManager._alias,Domain]
        self._ipcp_index = ipcp_index
        self._alias = f'DanteInterface:{DeviceName}'
        self._callback_properties = {'Connected':None,
                                     'Disconnected':None,
                                     'ReceiveData':None}
        self._properties_to_reformat = ['ReceiveData']
        self._query_properties_init = {}
        self._query_properties_always = {'Domain':[]}
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

    def Connect(self,timeout=None):
        """
        Connect to the device

        Parameters:	timeout (float) – time in seconds to attempt connection before giving up.
        Returns:	'Connected' or 'ConnectedAlready' or reason for failure
        Return type:	string
        """
        return self._Query('Connect',[timeout])


    def Disconnect(self):
        """
        Disconnect the session
        """
        self._Command('Disconnect',[])

    def Send(self,data):
        """
            Send string over Dante port

            Parameters:
                - data (bytes, string) – string to send out
        """
        if type(data) == str:
            data = data.encode()
        data = base64.b64encode(data).decode('utf-8')
        self._Command('Send',[data])





    def StartService(self,interface='LAN'):
        """
        Start the Dante Service.

        Parameters:	interface (string) – Defines the network interface connected to the Dante network ('LAN', or 'AVLAN')
        Returns:	'ServiceStarted' or a reason for failure
        The possible return values are:

        'ServiceStarted'
        'ServiceStartedAlready'
        'PortUnavailable'
        'InterfaceUnavailable: LAN'
        'InterfaceUnavailable: AVLAN'
        """
        return self._Query('StartService',[interface])
