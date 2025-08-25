from extronlib.engine.IpcpLink import ExtronNode
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from extronlib.device import ProcessorDevice
_debug = False
import traceback

class eBUSDevice(ExtronNode):
    """ Defines common interface to Extron eBUS panels

    ---

    Parameters:
        - Host (`ProcessorDevice`) - handle to Extron ProcessorDevice to which the eBUSDevice is connected
        - DeviceAlias (`string`) - Device Alias of the Extron device

    ---

    Properties:
        - DeviceAlias - Returns (`string`) - the device alias of the object
        - Host - Returns (extronlib.device.ProcessorDevice) - Handle to the Extron ProcessorDevice to which the eBUSDevice is connected.
        - ID - Returns (`int`) - device’s ID (set by DIP switch)
        - InactivityTime - Returns (`int`) - Seconds since last activity.  Note: 0 = Active, Nonzero = Time of inactivity
        - LidState - Returns (`string`) - the current lid state ('Opened' | 'Closed')
        - ModelName - Returns (`string`) - Model name of this device
        - PartNumber - Returns (`string`) - the part number of this device
        - SleepState - Returns (`string`) - the current sleep state of the device ('Asleep', 'Awake')
        - SleepTimer - Returns (`int`) - sleep timer timeout
        - SleepTimerEnabled - Returns (`bool`) - True if sleep timer is enabled

    ---

    Events:
        - `InactivityChanged` - (Event) Triggers at times specified by SetInactivityTime(`int`) after state transition of inactivity timer. The callback takes two Parameters. The first one is the eBUSDevice instance triggering the event and time with a float value of inactivity time in seconds.
        - `LidChanged` - (Event) Triggers when the Lid state changes.The callback takes two Parameters. The first one is the eBUSDevice instance triggering the event and the second is the current lid state ('Opened' | 'Closed').
        - `Offline` - (Event) Triggers when the device goes offline. The callback takes two Parameters. The first one is the extronlib.device instance triggering the event and the second one is a string ('Offline').
        - `Online` - (Event) Triggers when the device comes online. The callback takes two Parameters. The first one is the extronlib.device instance triggering the event and the second one is a string ('Online').
        - `SleepChanged` - (Event) Triggers when sleep state changes. The callback takes two Parameters. The first one is the eBUSDevice instance triggering the event and the second one is a string ('Asleep' | 'Awake').
    """



    _type='eBUSDevice'
    def __init__(self, Host: 'ProcessorDevice', DeviceAlias: str,ipcp_index=0) -> None:
        """
        eBUSDevice class constructor.

        ---

        Parameters:
            - Host (`object`) - handle to Extron ProcessorDevice to which the eBUSDevice is connected
            - DeviceAlias (`string`) - Device Alias of the Extron device
        """

        self.InactivityChanged = None
        """
        Event:
            - Triggers at times specified by SetInactivityTime() after state transition of inactivity timer.
            - The callback takes two arguments. The first one is the eBUSDevice instance triggering the event and time with a float value of inactivity time in seconds.

        ---

        ```
        PodiumPanel = eBUSDevice('Podium Panel')
        PodiumPanel.SetInactivityTime([3000, 3600])    # Fifty minutes and One hour

        @event(PodiumPanel, 'InactivityChanged')
        def UnoccupyRoom(Panel, time):
            if time == 3000:
                ShowWarning()
            else:
                ShutdownSystem()
        ```

        Note:
            Applies to EBP models only.
        """
        self.SleepChanged = None
        """
        Event:
            - Triggers when sleep state changes.
            - The callback takes two arguments. The first one is the eBUSDevice instance triggering the event and the second one is a string ('Asleep' or 'Awake').

        ---
        ```
        @event(PodiumPanel, 'SleepChanged')
        def HandleSleepChanged(Panel, state):
            print('{} Sleep State Changed: {}'.format(Panel.DeviceAlias, state))
        ```
        """
        self.LidChanged = None
        """
        Event:
            - Triggers when the Lid state changes.
            - The callback takes two arguments. The first one is the eBUSDevice instance triggering the event and the second is the current lid state ('Opened' or 'Closed').
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
        self._SleepTimerEnabled = False
        self.DeviceAlias = DeviceAlias
        self.Host = Host
        """ Handle to the Extron ProcessorDevice to which the eBUSDevice is connected. """
        self._InactivityTime = 0
        """Seconds since last activity.

        Note:
            - 0 = Active, Nonzero = Time of inactivity.
            - Applies to EBP models only.
        """
        self._SleepState = ''
        """	the current sleep state of the device ('Asleep', 'Awake')"""
        self._PartNumber = ''
        self._ModelName = ''
        self._LidState = ''
        """the current lid state ('Opened' or 'Closed')"""
        self._SleepTimer = 0
        """	sleep timer timeout"""
        self._ID = 0
        """device’s ID (set by DIP switch)"""
        self.ReceiveResponse = None


        self._args = [Host.DeviceAlias,DeviceAlias]
        self._ipcp_index = ipcp_index
        self._alias = f'{DeviceAlias}'
        self._callback_properties = {'InactivityChanged':{'var':'_InactivityTime','value index':1},
                                     'LidChanged':{'var':'_LidState','value index':1},
                                     'ReceiveResponse':None,
                                     'SleepChanged':{'var':'_SleepState','value index':1},
                                     'Offline':None,
                                     'Online':None}
        self._properties_to_reformat = []
        self._query_properties_init = {}
        self._query_properties_always = {'InactivityTime':[],
                                    'LidState':[],
                                    'ModelName':[],
                                    'PartNumber':[],
                                    'SleepState':[],
                                    'SleepTimer':[],
                                    'SleepTimerEnabled':[],
                                    'ID':[]}
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
    def InactivityTime(self):
        if 'InactivityTime' in self._query_properties_init_list:
            self._query_properties_init_list.remove('InactivityTime')
            self._InactivityTime = self._Query('InactivityTime',[])
        if 'InactivityTime' not in self._query_properties_always:
            return self._InactivityTime
        return self._Query('InactivityTime',[])
    @property
    def SleepState(self):
        if 'SleepState' in self._query_properties_init_list:
            self._query_properties_init_list.remove('SleepState')
            self._SleepState = self._Query('SleepState',[])
        if 'SleepState' not in self._query_properties_always:
            return self._SleepState
        return self._Query('SleepState',[])
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
    @property
    def LidState(self):
        if 'LidState' in self._query_properties_init_list:
            self._query_properties_init_list.remove('LidState')
            self._LidState = self._Query('LidState',[])
        if 'LidState' not in self._query_properties_always:
            return self._LidState
        return self._Query('LidState',[])
    @property
    def SleepTimer(self):
        if 'SleepTimer' in self._query_properties_init_list:
            self._query_properties_init_list.remove('SleepTimer')
            self._SleepTimer = self._Query('SleepTimer',[])
        if 'SleepTimer' not in self._query_properties_always:
            return self._SleepTimer
        return self._Query('SleepTimer',[])
    @property
    def SleepTimerEnabled(self):
        if 'SleepTimerEnabled' in self._query_properties_init_list:
            self._query_properties_init_list.remove('SleepTimerEnabled')
            self._SleepTimerEnabled = self._Query('SleepTimerEnabled',[])
        if 'SleepTimerEnabled' not in self._query_properties_always:
            return self._SleepTimerEnabled
        return self._Query('SleepTimerEnabled',[])
    @property
    def ID(self):
        if 'ID' in self._query_properties_init_list:
            self._query_properties_init_list.remove('ID')
            self._ID = self._Query('ID',[])
        if 'ID' not in self._query_properties_always:
            return self._ID
        return self._Query('ID',[])









    def Click(self, count: int=1, interval: int=None) -> None:
        """ Play default buzzer sound on applicable device

        ---

        Parameters:
            - count (`int`) - number of buzzer sound to play
            - interval (`int`) - time gap in millisecond between consecutive sounds
        """
        self._Command('Click',[count,interval])

    def GetMute(self, name: str) -> str:
        """ Get the mute state for the given channel

        ---

        The defined channel names are:
            - 'Click' - button click volume

        ---

        Parameters:
            - name (`string`) - name of channel.

        ---

        Returns
            - mute state ('On' | 'Off') (`string`)
        """
        self._Query('GetMute',[name])

    def Reboot(self) -> None:
        """Performs a soft restart of this device – this is equivalent to rebooting a PC."""
        self._Command('Reboot',[])

    def SendCommand(self, command: str, value) -> None:
        """Send command to eBUSDevice.

        ---

        Args:
            - command (`string`): command name to issue
            - value (`int | tuple[int]`): command specific value to pass with commend

        ---

        Example:
        ```
        VoiceLiftDevice.SendCommand('Chime', 1)     # Enable Chime
        VoiceLiftDevice.SendCommand('Usage')        # Query usage
        ```

        ---

        Note:
            - For supported eBUS devices.
            - See device documentation for supported commands.
        """
        ...
        self._Command('SendCommand',[command,value])

    def SetInactivityTime(self, times: list) -> None:
        """ Set the inactivity times of the eBUSDevice. When each time expires, the InactivityChanged event will be triggered. All times are absolute.

        ---

        Parameters:
            - times (`list of ints`) - list of times. Each time in whole seconds

        ---

        Example:
        ```
        PodiumPanel = eBUSDevice('Podium Panel')
        PodiumPanel.SetInactivityTime([3000, 3600])    # Fifty minutes and One hour

        @event(PodiumPanel, 'InactivityChanged')
        def UnoccupyRoom(Panel, time):
            if time == 3000:
                ShowWarning()
            else:
                ShutdownSystem()
        ```

        ---

        Note:
            - Applies to EBP models only.
        """
        self._Command('SetInactivityTime',[times])

    def SetMute(self, name: str, mute: str) -> None:
        """ Set the mute state for the given channel

        ---

        The defined channel names are:
            - `Click` - button click volume

        ---

        Parameters:
            - name (`string`) - name of channel.
            - mute (`string`) - mute state ('On' | 'Off')

        ---

        Example:
        ```
        @event(ToggleMute, 'Pressed')
        def toggleMute(button, state):
            if PodiumEBP.GetMute('Click') == 'On':
                PodiumEBP.SetMute('Click', 'Off')
            else:
                PodiumEBP.SetMute('Click', 'On')
        ```
        """
        self._Command('SetMute',[name,mute])

    def SetSleepTimer(self, state, duration: int=None) -> None:
        """ Enable/disable sleep timer. Either 'On' | True enables sleep timer. 'Off' | False disables sleep timer.

        ---

        Parameters:
            - state (bool, string) - whether to enable the sleep timer
            - (optional) duration (`int`) - time in seconds to sleep (`int`)

        ---

        Example:
        ```
        @event(ButtonObject, 'Pressed')
        def Initialize(button, state):
            PodiumPanel.SetSleepTimer('On', 60)
        ```
        """
        self._Command('SetSleepTimer',[state,duration])

    def Sleep(self) -> None:
        """ Force the device to sleep immediately """
        self._Command('Sleep',[])

    def Wake(self) -> None:
        """ Force the device to wake up immediately """
        self._Command('Wake',[])
