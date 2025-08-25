from extronlib.engine.IpcpLink import ExtronNode
_debug = False
import traceback

class UIDevice(ExtronNode):
    """Entity to communicate with Extron Device featuring user interactive input.

    Note:
        - DeviceAlias must be a valid device Device Alias of an Extron device in the system.
        - If the part number is provided, the device will trigger a warning message in the program log if it does not match the connected device.

    ---

    Arguments:
        - DeviceAlias (string) - Device Alias of the Extron device
        - (optional) PartNumber  (string) - device’s part number

    ---

    Parameters:
        - `AmbientLightValue` - Returns (int) - current ambient light value
        - `AutoBrightness` - Returns (bool) - current auto brightness state
        - `Brightness` - Returns (int) - current LCD brightness level
        - `DeviceAlias` - Returns (string) - the device alias of the object
        - `DisplayState` - Returns (string) - the current display state of the device ('On', 'Off'). Note  This property is applicable to TLI only.
        - `DisplayTimer` - Returns (int) - Return display timer timeout seconds
        - `DisplayTimerEnabled` - Returns (bool) - current state of the display timer
        - `FirmwareVersion` - Returns (string) - the firmware version of this device
        - `Hostname` - Returns (string) - the hostname of this device
        - `IPAddress` - Returns (string) - IP address of this device
        - `InactivityTime` - Returns (string) - Seconds since last activity. Note 0 = Active, Nonzero = Time of inactivity.
        - `LidState` - Returns (string) - the current lid state ('Opened' or 'Closed')
        - `LightDetectedState` - Returns (string) - State of light detection. ('Detected', 'Not Detected')
        - `MACAddress` - Returns (string) -MAC address of this device. Note  For dual NIC devices, the LAN address is returned.
        - `ModelName` - Returns (string) - Model name of this device
        - `MotionDecayTime` - Returns (int) - the period of time to trigger MotionDetected event after last motion was detected. The default (and minimum) value is 10 seconds.
        - `MotionState` - Returns (string) - the state of the Motion sensor (e.g. Motion, No Motion)
        - `PartNumber` - Returns (string) - the part number of this device
        - `SerialNumber` - Returns (string) - Serial number of this device
        - `SleepState` - Returns (string) - the current sleep state of the device ('Asleep', 'Awake')
        - `SleepTimer` - Returns (int) - sleep timer timeout
        - `SleepTimerEnabled` - Returns (bool) - True if sleep timer is enabled
        - `UserUsage` - Returns (tuple of ints) - user data usage of this device in KB (used, total).
        - `WakeOnMotion` - Returns (bool) - current wake on motion state

    ---

    Events:
        - `BrightnessChanged`   (Event)   Triggers when LCD brightness has changed. The callback takes two arguments. The first one is the UIDevice instance triggering the event and the second one is the current brightness level as an integer.
        - `HDCPStatusChanged`   (Event)   Triggers when HDCP Status changes. The callback takes two arguments. The first one is the UIDevice instance triggering the event and state with a tuple  (Input, Status).
        - `InactivityChanged`   (Event)   Triggers at times specified by SetInactivityTime() after state transition of inactivity timer. The callback takes two arguments. The first one is the UIDevice instance triggering the event and time with a float value of inactivity time in seconds.
        - `InputPresenceChanged`   (Event)   Triggers when Input Presence changes. The callback takes two arguments. The first one is the UIDevice instance triggering the event and state with a tuple  (Input, Status).
        - `LidChanged`   (Event)   Triggers when the Lid state changes. The callback takes two arguments. The first one is the UIDevice instance triggering the event and the second is the current lid state ('Opened' or 'Closed').
        - `LightChanged`   (Event)   Triggers when ambient light changes. The callback takes two arguments. The first one is the UIDevice instance triggering the event and the second is the ambient light level in the range of 0 ~ 255.
        - `MotionDetected`   (Event)   Triggers when Motion is detected. The callback takes two arguments. The first one is the UIDevice instance triggering the event and the second one is a string ('Motio' or 'No Motion')
        - `Offline`   (Event)   Triggers when the device goes offline. The callback takes two arguments. The first one is the extronlib.device instance triggering the event and the second one is a string ('Offline').
        - `Online`   (Event)   Triggers when the device comes online. The callback takes two arguments. The first one is the extronlib.device instance triggering the event and the second one is a string ('Online').
        - `SleepChanged`   (Event)   Triggers when sleep state changes. The callback takes two arguments. The first one is the UIDevice instance triggering the event and the second one is a string ('Asleep' or 'Awake').

    ---

    Example:
    ```
    # Create Primary Processor
    ConfRoom = ProcessorDevice('Main')

    # Create Secondary Processor, Confirm Partnumber
    ConfRoom3 = ProcessorDevice('profRobertsRm', '60-1234-01')

    # Create Touch Panel
    PodiumTLP = UIDevice('Podium TLP')

    # Create System Switcher AV Device
    SystemSwitcher = SPDevice('SysSwitcher')
    ```
    """

    _type='UIDevice'
    def __init__(self, DeviceAlias: str, PartNumber: str=None,ipcp_index=0) -> None:
        """
        UIDevice class constructor.

        Arguments:
            - DeviceAlias (string) - Device Alias of the Extron device
            - (optional) PartNumber  (string) - device’s part number
        """

        self.DeviceAlias = DeviceAlias
        self._PartNumber = ''
        self._AmbientLightValue = 0
        self._AutoBrightness = False
        self._Brightness = 100
        self.BrightnessChanged = None
        """
        ## Event:
            - Triggers when LCD brightness has changed.

        The callback takes two arguments. The first one is the UIDevice instance triggering the event and the second one is the current brightness level as an integer.

        ---

        Example:
        ```
        @event(PodiumTLP, 'BrightnessChanged')
        def HandleBrightnessChanged(tlp, brightness):
            print('{} Brightness Changed: {}'.format(tlp.DeviceAlias, brightness))
        ```
        """
        self._DisplayState = ''
        """	the current display state of the device ('On', 'Off')

        Note:
            - This property is applicable to TLI only.
        """
        self._DisplayTimer = ''
        """Return display timer timeout seconds"""
        self._DisplayTimerEnabled = False
        self._FirmwareVersion = ''
        self.HDCPStatusChanged = None
        self._HDCPStatus = ''
        """
        ## Event:
            - Triggers when HDCP Status changes.

        The callback takes two arguments. The first one is the UIDevice instance triggering the event and state with a tuple: (Input, Status).

        ---

        Example:
        ```
        @event(PodiumTLP, 'HDCPStatusChanged')
        def HandleHDCPStatusChangedChange(tlp, state):
            if state[0] == 'HDMI' and not state[1]:
                PodiumTLP.ShowPopup('No HDCP')
        ```
        """
        self._Hostname = ''
        self._IPAddress = ''
        self.InactivityChanged = None
        """
        ## Event:
            - Triggers at times specified by SetInactivityTime() after state transition of inactivity timer.

        The callback takes two arguments. The first one is the UIDevice instance triggering the event and time with a float value of inactivity time in seconds.

        ---

        Example:
        ```
        PodiumTLP = UIDevice('Podium TLP')
        PodiumTLP.SetInactivityTime([3000, 3600])    # Fifty minutes and One hour

        @event(PodiumTLP, 'InactivityChanged')
        def UnoccupyRoom(tlp, time):
            if time == 3000:
                ShowWarning()
            else:
                ShutdownSystem()
        ```
        """
        self._InactivityTime = 0
        """	Seconds since last activity.

        Note:
            - 0 = Active, Nonzero = Time of inactivity.
        """
        self.InputPresenceChanged = None
        self._InputPresence = ''
        """
        ## Event:
            - Triggers when Input Presence changes.

        The callback takes two arguments. The first one is the UIDevice instance triggering the event and state with a tuple: (Input, Status).

        ---

        Example:
        ```
        @event(PodiumTLP, 'InputPresenceChanged')
        def HandleInputPresenceChanged(tlp, state):
            if state[0] == 'HDMI' and not state[1]:
                if PodiumTLP.GetInputPresence('XTP'):
                    PodiumTLP.SetInput('XTP')
                else:
                    PodiumTLP.ShowPopup('No Input Available')
        ```
        """
        self.LidChanged = None
        """
        ## Event:
            - Triggers when the Lid state changes.

        The callback takes two arguments. The first one is the UIDevice instance triggering the event and the second is the current lid state ('Opened' or 'Closed').
        """
        #self._LidState = ''
        """the current lid state ('Opened' or 'Closed')"""
        self.LightChanged = None
        """
        ## Event:
            - Triggers when ambient light changes

        The callback takes two arguments. The first one is the UIDevice instance triggering the event and the second is the ambient light level in the range of 0 ~ 255.
        """
        self._LightDetectedState = ''

        self._LinkLicenses = []
        """State of light detection. ('Detected', 'Not Detected')"""
        self._MACAddress = ''
        self._ModelName = ''
        self._MotionDecayTime = 10
        """	the period of time to trigger MotionDetected event after last motion was detected. The default (and minimum) value is 10 seconds."""
        self.MotionDetected = None
        """
        ## Event:
            - Triggers when Motion is detected.

        The callback takes two arguments. The first one is the UIDevice instance triggering the event and the second one is a string ('Motion' or 'No Motion').
        """
        self._MotionState = ''
        """the state of the Motion sensor (e.g. Motion, No Motion)"""
        self.Offline = None
        """
        ## Event:
            - Triggers when the device goes offline.

        The callback takes two arguments. The first one is the extronlib.device instance triggering the event and the second one is a string ('Offline').
        """
        self.Online = None
        """
        ## Event:
            - Triggers when the device comes online.

        The callback takes two arguments. The first one is the extronlib.device instance triggering the event and the second one is a string ('Online').
        """
        self._PartNumber = ''
        self._SerialNumber = ''
        self.SleepChanged = None
        """
        ## Event:
            - Triggers when sleep state changes.

        The callback takes two arguments. The first one is the UIDevice instance triggering the event and the second one is a string ('Asleep' or 'Awake').


        ---

        Example:
        ```
        @event(PodiumTLP, 'SleepChanged')
        def HandleSleepChanged(tlp, state):
            print('{} Sleep State Changed: {}'.format(tlp.DeviceAlias, state))
        ```
        """
        self._SleepState = ''
        """the current sleep state of the device ('Asleep', 'Awake')"""
        self._SleepTimer = 0
        """sleep timer timeout"""
        self._SleepTimerEnabled = False
        self._UserUsage = [0,0]
        """user data usage of this device in KB (used, total)."""
        self._WakeOnMotion = True
        self._OverTemperature = 0
        """
        Returns: the current operating temperature value, in degrees Centigrade, as a differential from the product maximum operating temperature.

        Return type:	int

        Note:
            - This feature only supported by the TLI Pro 201 TouchLink Interface.

        ## Warning:
            - Not implemented.

        ---

        Example:
        ```
        # If the product is 5 degrees C over maximum operating temperature, this
        # prints 5.
        print(PoduiumTLP.OverTemperature)

        # If the product is 15 degrees C below maximum operating temperature, this
        # prints -15.
        print(PoduiumTLP.OverTemperature)
        ```
        """
        self.OverTemperatureChanged = None
        """
        ## Event:
            - Triggers when Over Temperature changes.

        The callback takes two arguments. The first one is the UIDevice instance triggering the event and the second is the new temperature differential as an integer.

        Note:
            - This event triggers for each 1 degree change but no more than once every 10 seconds if the temperature is oscillating.
            - This feature only supported by the TLI Pro 201 TouchLink Interface
            - New in version 1.1.

        ---

        Example:
        ```
        @event(PodiumTLP, 'OverTemperatureChanged')
        def HandleOverTemperatureChanged(tlp, temp):
            print('Podium TLP OverTemperature is ' + str(temp))
        ```
        """
        self.OverTemperatureWarning = None
        """
        ## Event:
            - Triggers when the product’s operating temperature exceeds the maximum by 5 percent.

        Note:
            - This event retriggers once every minute until the operating temperature falls below the maximum operating temperature.
            - This feature only supported by the TLI Pro 201 TouchLink Interface
            - New in version 1.1.

        The callback takes two arguments. The first one is the UIDevice instance triggering the event and the second is current operating temperature in degrees Centigrade over the maximum as an integer.

        ---

        Example:
        ```
        @event(PodiumTLP, 'OverTemperatureWarning')
        def HandleOverTemperatureWarning(device, temp):
            print('The podium TLP is {} degrees over maximum operating temperature.'.format(temp))
        ```
        """
        self.OverTemperatureWarningState = False
        """
        Returns:
            - Whether this device is currently over temperature.

        Return type:
            - bool

        Note:
            - This feature only supported by the TLI Pro 201 TouchLink Interface.
            - New in version 1.1.

        ---

        Example:
        ```
        if PodiumTLP.OverTemperatureWarningState:
            print('Podium TLP is over maximum temperature.')
        ```
        """
        self.OverTemperatureWarningStateChanged = None
        """
        ## Event:
            - Triggers when the product’s operating temperature warning changes state.

        Note:
            - This feature only supported by the TLI Pro 201 TouchLink Interface.
            - New in version 1.1.

        The callback takes two arguments. The first one is the UIDevice instance triggering the event and the second is current state of the over temperature warning as a bool.

        ---

        Example:
        ```
        @event(PodiumTLP, 'OverTemperatureWarningStateChanged')
        def HandleOverTemperatureWarningStateChanged(device, state):
            if state:
                print('The podium TLP is over maximum operating temperature.')
            else:
                print('The podium TLP operating temperature is normal.')
        ```
        """
        self._SystemSettings = {}
        """
        Returns:
            - a dictionary of data describing the settings (defined in Toolbelt) of this device

        Return type:
            - dict

        ---

        Example:
        ```
        {
            'Network': {
                'LAN': [
                        -   'DNSServers': ['192.168.1.1',],
                        -   'Gateway': '192.168.254.1',
                        -   'Hostname': 'ConfRoom',
                        -   'IPAddress': '192.168.254.250',
                        -   'SubnetMask': '255.255.255.0',
                        -   'SearchDomains': ['extron.com',],
                ],
            },
            'ProgramInformation': {
                'Author': 'jdoe',
                'DeviceName': 'TLP Pro 720T : 192.168.254.251',
                'FileLoaded': 'GS Project.gs',
                'LastUpdated': '1/23/2016 9:08:29 AM',
                'SoftwareVersion': '1.0.2.195',
            }
        }
        ```
        """
        self._args = [DeviceAlias,PartNumber]
        self._ipcp_index = ipcp_index
        self._alias = f'{DeviceAlias}'
        self._callback_properties = {'BrightnessChanged':{'var':'_Brightness','value index':1},
                                     'HDCPStatusChanged':{'var':'_HDCPStatus','value index':1},
                                     'InactivityChanged':{'var':'_InactivityTime','value index':1},
                                     'InputPresenseChanged':{'var':'_InputPresence','value index':1},
                                     'LidChanged':{'var':'_LidState','value index':1},
                                     'LightChanged':{'var':'_LightDetectedState','value index':1},
                                     'MotionDetected':None,
                                     'Offline':None,
                                     'Online':None,
                                     'SleepChanged':{'var':'_SleepState','value index':1}}
        self._properties_to_reformat = []
        self._query_properties_init = {}
        self._query_properties_always = {'AmbientLightValue':[],
                                          'AutoBrightness':[],
                                          'Brightness':[],
                                          'DisplayState':[],
                                          'DisplayTimer':[],
                                          'DisplayTimerEnabled':[],
                                          'HDCPStatus':[],
                                          'FirmwareVersion':[],
                                          'Hostname':[],
                                          'IPAddress':[],
                                          'InactivityTime':[],
                                          'InputPresence':[],
                                          'LidState':[],
                                          'LightDetectedState':[],
                                          'LinkLicenses':[],
                                          'MACAddress':[],
                                          'ModelName':[],
                                          'MotionDecayTime':[],
                                          'MotionState':[],
                                          'PartNumber':[],
                                          'SerialNumber':[],
                                          'SleepTimer':[],
                                          'SleepTimerEnabled':[],
                                          'UserUsage':[],
                                          'WakeOnMotion':[],
                                          'OverTemperature':[],
                                          'SystemSettings':[]}
        self._query_properties_always = {}
        super().__init__(self)
        self._initialize_values()
    def _initialize_values(self):
        self._query_properties_init_list = list(self._query_properties_init.keys())
    def __format_parsed_update_value(self,property,value):
        if property in self._properties_to_reformat:
            if property == 'UserUsage':
                value = tuple(value)
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
    def AmbientLightValue(self):
        if 'AmbientLightValue' in self._query_properties_init_list:
            self._query_properties_init_list.remove('AmbientLightValue')
            self._AmbientLightValue = self._Query('AmbientLightValue',[])
        if 'AmbientLightValue' not in self._query_properties_always:
            return self._AmbientLightValue
        return self._Query('AmbientLightValue',[])
    @property
    def AutoBrightness(self):
        if 'AutoBrightness' in self._query_properties_init_list:
            self._query_properties_init_list.remove('AutoBrightness')
            self._AutoBrightness = self._Query('AutoBrightness',[])
        if 'AutoBrightness' not in self._query_properties_always:
            return self._AutoBrightness
        return self._Query('AutoBrightness',[])
    @property
    def Brightness(self):
        if 'Brightness' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Brightness')
            self._Brightness = self._Query('Brightness',[])
        if 'Brightness' not in self._query_properties_always:
            return self._Brightness
        return self._Query('Brightness',[])
    @property
    def DisplayState(self):
        if 'DisplayState' in self._query_properties_init_list:
            self._query_properties_init_list.remove('DisplayState')
            self._DisplayState = self._Query('DisplayState',[])
        if 'DisplayState' not in self._query_properties_always:
            return self._DisplayState
        return self._Query('DisplayState',[])
    @property
    def DisplayTimer(self):
        if 'DisplayTimer' in self._query_properties_init_list:
            self._query_properties_init_list.remove('DisplayTimer')
            self._DisplayTimer = self._Query('DisplayTimer',[])
        if 'DisplayTimer' not in self._query_properties_always:
            return self._DisplayTimer
        return self._Query('DisplayTimer',[])
    @property
    def DisplayTimerEnabled(self):
        if 'DisplayTimerEnabled' in self._query_properties_init_list:
            self._query_properties_init_list.remove('DisplayTimerEnabled')
            self._DisplayTimerEnabled = self._Query('DisplayTimerEnabled',[])
        if 'DisplayTimerEnabled' not in self._query_properties_always:
            return self._DisplayTimerEnabled
        return self._Query('DisplayTimerEnabled',[])
    @property
    def HDCPStatus(self):
        if 'HDCPStatus' in self._query_properties_init_list:
            self._query_properties_init_list.remove('HDCPStatus')
            self._HDCPStatus = self._Query('HDCPStatus',[])
        if 'HDCPStatus' not in self._query_properties_always:
            return self._HDCPStatus
        return self._Query('HDCPStatus',[])
    @property
    def FirmwareVersion(self):
        if 'FirmwareVersion' in self._query_properties_init_list:
            self._query_properties_init_list.remove('FirmwareVersion')
            self._FirmwareVersion = self._Query('FirmwareVersion',[])
        if 'FirmwareVersion' not in self._query_properties_always:
            return self._FirmwareVersion
        return self._Query('FirmwareVersion',[])
    @property
    def Hostname(self):
        if 'Hostname' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Hostname')
            self._Hostname = self._Query('Hostname',[])
        if 'Hostname' not in self._query_properties_always:
            return self._Hostname
        return self._Query('Hostname',[])
    @property
    def IPAddress(self):
        if 'IPAddress' in self._query_properties_init_list:
            self._query_properties_init_list.remove('IPAddress')
            self._IPAddress = self._Query('IPAddress',[])
        if 'IPAddress' not in self._query_properties_always:
            return self._IPAddress
        return self._Query('IPAddress',[])
    @property
    def InactivityTime(self):
        if 'InactivityTime' in self._query_properties_init_list:
            self._query_properties_init_list.remove('InactivityTime')
            self._InactivityTime = self._Query('InactivityTime',[])
        if 'InactivityTime' not in self._query_properties_always:
            return self._InactivityTime
        return self._Query('InactivityTime',[])
    @property
    def InputPresence(self):
        if 'InputPresence' in self._query_properties_init_list:
            self._query_properties_init_list.remove('InputPresence')
            self._InputPresence = self._Query('InputPresence',[])
        if 'InputPresence' not in self._query_properties_always:
            return self._InputPresence
        return self._Query('InputPresence',[])
    @property
    def LidState(self):
        if 'LidState' in self._query_properties_init_list:
            self._query_properties_init_list.remove('LidState')
            self._LidState = self._Query('LidState',[])
        if 'LidState' not in self._query_properties_always:
            return self._LidState
        return self._Query('LidState',[])
    @property
    def LightDetectedState(self):
        if 'LightDetectedState' in self._query_properties_init_list:
            self._query_properties_init_list.remove('LightDetectedState')
            self._LightDetectedState = self._Query('LightDetectedState',[])
        if 'LightDetectedState' not in self._query_properties_always:
            return self._LightDetectedState
        return self._Query('LightDetectedState',[])
    @property
    def LinkLicenses(self):
        if 'LinkLicenses' in self._query_properties_init_list:
            self._query_properties_init_list.remove('LinkLicenses')
            self._LinkLicenses = self._Query('LinkLicenses',[])
        if 'LinkLicenses' not in self._query_properties_always:
            return self._LinkLicenses
        return self._Query('LinkLicenses',[])
    @property
    def MACAddress(self):
        if 'MACAddress' in self._query_properties_init_list:
            self._query_properties_init_list.remove('MACAddress')
            self._MACAddress = self._Query('MACAddress',[])
        if 'MACAddress' not in self._query_properties_always:
            return self._MACAddress
        return self._Query('MACAddress',[])
    @property
    def ModelName(self):
        if 'ModelName' in self._query_properties_init_list:
            self._query_properties_init_list.remove('ModelName')
            self._ModelName = self._Query('ModelName',[])
        if 'ModelName' not in self._query_properties_always:
            return self._ModelName
        return self._Query('ModelName',[])
    @property
    def MotionDecayTime(self):
        if 'MotionDecayTime' in self._query_properties_init_list:
            self._query_properties_init_list.remove('MotionDecayTime')
            self._MotionDecayTime = self._Query('MotionDecayTime',[])
        if 'MotionDecayTime' not in self._query_properties_always:
            return self._MotionDecayTime
        return self._Query('MotionDecayTime',[])
    @property
    def MotionState(self):
        if 'MotionState' in self._query_properties_init_list:
            self._query_properties_init_list.remove('MotionState')
            self._MotionState = self._Query('MotionState',[])
        if 'MotionState' not in self._query_properties_always:
            return self._MotionState
        return self._Query('MotionState',[])
    @property
    def PartNumber(self):
        if 'PartNumber' in self._query_properties_init_list:
            self._query_properties_init_list.remove('PartNumber')
            self._PartNumber = self._Query('PartNumber',[])
        if 'PartNumber' not in self._query_properties_always:
            return self._PartNumber
        return self._Query('PartNumber',[])
    @property
    def SerialNumber(self):
        if 'SerialNumber' in self._query_properties_init_list:
            self._query_properties_init_list.remove('SerialNumber')
            self._SerialNumber = self._Query('SerialNumber',[])
        if 'SerialNumber' not in self._query_properties_always:
            return self._SerialNumber
        return self._Query('SerialNumber',[])
    @property
    def SleepState(self):
        if 'SleepState' in self._query_properties_init_list:
            self._query_properties_init_list.remove('SleepState')
            self._SleepState = self._Query('SleepState',[])
        if 'SleepState' not in self._query_properties_always:
            return self._SleepState
        return self._Query('SleepState',[])
    @property
    def SleepTimerEnabled(self):
        if 'SleepTimerEnabled' in self._query_properties_init_list:
            self._query_properties_init_list.remove('SleepTimerEnabled')
            self._SleepTimerEnabled = self._Query('SleepTimerEnabled',[])
        if 'SleepTimerEnabled' not in self._query_properties_always:
            return self._SleepTimerEnabled
        return self._Query('SleepTimerEnabled',[])
    @property
    def UserUsage(self):
        if 'UserUsage' in self._query_properties_init_list:
            self._query_properties_init_list.remove('UserUsage')
            self._UserUsage = self._Query('UserUsage',[])
        if 'UserUsage' not in self._query_properties_always:
            return self._UserUsage
        return self._Query('UserUsage',[])
    @property
    def WakeOnMotion(self):
        if 'WakeOnMotion' in self._query_properties_init_list:
            self._query_properties_init_list.remove('WakeOnMotion')
            self._WakeOnMotion = self._Query('WakeOnMotion',[])
        if 'WakeOnMotion' not in self._query_properties_always:
            return self._WakeOnMotion
        return self._Query('WakeOnMotion',[])
    @property
    def OverTemperature(self):
        if 'OverTemperature' in self._query_properties_init_list:
            self._query_properties_init_list.remove('OverTemperature')
            self._OverTemperature = self._Query('OverTemperature',[])
        if 'OverTemperature' not in self._query_properties_always:
            return self._OverTemperature
        return self._Query('OverTemperature',[])
    @property
    def SystemSettings(self):
        if 'SystemSettings' in self._query_properties_init_list:
            self._query_properties_init_list.remove('SystemSettings')
            self._SystemSettings = self._Query('SystemSettings',[])
        if 'SystemSettings' not in self._query_properties_always:
            return self._SystemSettings
        return self._Query('SystemSettings',[])



    def Click(self, count: int=1, interval: float=None) -> None:
        """ Play default buzzer sound on applicable device

        Arguments:
            - (optional) count (int) - number of buzzer sound to play
            - (optional) interval (float) - time gap between the starts of consecutive buzzer sounds

        Note:
            If count is greater than 1, interval must be provided.
        """
        self._Command('Click',[])

    def GetHDCPStatus(self, videoInput: str) -> bool:
        """ Return the current HDCP Status for the given input.

        Arguments:
            - videoInput (string) - input ('HDMI' or 'XTP')

        ---

        Returns:
            - True or False (bool)

        ---

        Example:
        ```
        HDCPStatus = PodiumTLP.GetHDCPStatus('XTP')
        if not HDCPStatus:
            PodiumTLP.ShowPopup('No HDCP')
        ```
        """
        return self._Query('GetHDCPStatus',[videoInput])

    def  GetInputPresence(self, videoInput: str) -> bool:
        """ Return the current input presence status for the given input.

        Arguments:
            - videoInput (string) - input ('HDMI' or 'XTP')

        ---

        Returns:
            - True or False (bool)

        ---

        Example:
        ```
        InputPresence = PodiumTLP.GetInputPresence('XTP')
        if not InputPresence:
            PodiumTLP.ShowPopup('No XTP')
        ```
        """
        return self._Query('GetInputPresence',[videoInput])

    def  GetMute(self, name: str) -> str:
        """ Get the mute state for the given channel

        The defined channel names are:
            - 'Master' - the master volume
            - 'Speaker' - the built-in speakers
            - 'Line' - the line out
            - 'Click' - button click volume
            - 'Sound' - sound track playback volume
            - 'HDMI' - HDMI input volume
            - 'XTP' - XTP input volume

        ---

        Arguments:
            - name (string) - name of channel.

        ---

        Returns:
            - mute state ('On' or 'Off') (string)

        ---

        Example:
        ```
        @event(ToggleMute, 'Pressed')
        def toggleMute(button, state):
            if PodiumTLP.GetMute('HDMI') == 'On':
                PodiumTLP.SetMute('HDMI', 'Off')
            else:
                PodiumTLP.SetMute('HDMI', 'On')
        ```
        """
        return self._Query('GetMute',[name])

    def  GetVolume(self, name: str) -> int:
        """ Return current volume level for the given channel

        The defined channel names are:
            - 'Master' - the master volume
            - 'Click' - button click volume
            - 'Sound' - sound track playback volume
            - 'HDMI' - HDMI input volume
            - 'XTP' - XTP input volume

        ---

        Arguments:
            - name (string) - name of volume channel.

        ---

        Returns:
            - volume level (int)

        ---

        Example:
        ```
        @event(ButtonObject, 'Pressed')
        def RefreshPage(button, state):
            currentVolume = PodiumTLP.GetVolume('HDMI')
            ...
        ```
        """
        return self._Query('GetVolume',[name])

    def HideAllPopups(self) -> None:
        """ Dismiss all popup pages """
        self._Command('HideAllPopups',[])

    def HidePopup(self, popup) -> None:
        """ Hide popup page

        Arguments:
            - popup (int, string) - popup page number or name
        """
        self._Command('HidePopup',[popup])

    def HidePopupGroup(self, group: int) -> None:
        """ Hide all popup pages in a popup group

        Arguments:
            - group (int) - popup group number

        ---

        Example:
        ```
        @event(ButtonObject, 'Pressed')
        def Reset(button, state):
            PodiumTLP.HidePopupGroup(1)
        ```
        """
        self._Command('HidePopupGroup',[group])

    def PlaySound(self, filename: str) -> None:
        """ Play a sound file identified by the filename

        Arguments:
            - filename (string) - name of sound file

        ---

        Note:
            - Only WAV files can be played.
            - A subsequent call will preempt the currently playing file.
            - Sound file must be added to the project file.

        ---

        Example:
        ```
        @event(ButtonObject, 'Pressed')
        def OccupyRoom(button, state):
            PodiumTLP.SetLEDBlinking(65533, 'Slow', ['Red', 'Off'])
            PodiumTLP.PlaySound('startup.wav')
        ```
        """
        self._Command('PlaySound',[filename])

    def Reboot(self) -> None:
        """Performs a soft restart of this device – this is equivalent to rebooting a PC."""
        self._Command('Reboot',[])

    def SetAutoBrightness(self, state) -> None:
        """ Set auto brightness state. Either 'On' or True turns on auto brightness. 'Off' or False turns off auto brightness.

        Arguments:
            - state (bool, string) - whether to enable auto brightness

        ---

        Example:
        ```
        @event(ButtonObject, 'Pressed')
        def Initialize(button, state):
            PodiumTLP.SetAutoBrightness('On')
        ```
        """
        self._Command('SetAutoBrightness',[state])

    def SetBrightness(self, level: int) -> None:
        """ Set LCD screen brightness level

        Arguments:
            - level (int) - brightness level from 0 ~ 100

        ---

        Example:
        ```
        @event(ButtonObject, 'Pressed')
        def Initialize(button, state):
            PodiumTLP.SetAutoBrightness('Off')
            PodiumTLP.SetBrightness(50)
        ```
        """
        self._Command('SetBrightness',[level])

    def SetDisplayTimer(self, state, timeout: int) -> None:
        """ Enable/disable display timer. Either 'On' or True enables display timer. 'Off' or False disables display timer.

        Note:
            - Display timer is applicable to TLI only.

        Arguments:
            - state (bool, string) - whether to enable the display timer
            - timeout (int) - time in seconds before turn off the display

        ---

        Example:
        ```
        @event(ButtonObject, 'Pressed')
        def Initialize(button, state):
            PodiumTLP.SetDisplayTimer(True, 180)
        ```
        """
        self._Command('SetDisplayTimer',[state, timeout])

    def SetInactivityTime(self, times: list) -> None:
        """ Set the inactivity times of the UIDevice. When each time expires, the InactivityChanged event will be triggered. All times are absolute.

        Arguments:
            - times (list of ints) - list of times. Each time in whole seconds

        ---

        Example:
        ```
        PodiumTLP = UIDevice('Podium TLP')
        PodiumTLP.SetInactivityTime([3000, 3600])    # Fifty minutes and One hour

        @event(PodiumTLP, 'InactivityChanged')
        def UnoccupyRoom(tlp, time):
            if time == 3000:
                ShowWarning()
            else:
                ShutdownSystem()
        ```
        """
        self._Command('SetInactivityTime',[times])

    def SetInput(self, videoInput: str) -> None:
        """ Sets the input. Inputs must be published for each device.

        Arguments:
            - videoInput (string) - input to select ('HDMI' or 'XTP')

        ---

        Example:
            >>> PodiumTLP.SetInput('HDMI')
        """
        self._Command('SetInput',[videoInput])

    def SetLEDBlinking(self, ledId: int, rate: str, stateList: list) -> None:
        """ Make the LED cycle, at ADA compliant rates, through each of the states provided.

        ---

        Blink rates:
        ```
        +-----------+-------------+
        | Rate      | Frequency   |
        +===========+=============+
        | Slow      | 0.5 Hz      |
        +-----------+-------------+
        | Medium    | 1 Hz        |
        +-----------+-------------+
        | Fast      | 2 Hz        |
        +-----------+-------------+
        ```
        Note:
            - Using this function will blink in unison with other LEDs.

        ---

        Arguments:
            - ledId (int) - LED id
            - rate (string) - ADA compliant blink rate. ('Slow', 'Medium', 'Fast')
            - stateList (list of strings) - List of colors

        Note:
            - Available colors are Red, Green, and Off.

        ---

        Example:
        ```
        PodiumTLP = UIDevice('Podium TLP')

        @event(ButtonObject, 'Pressed')
        def UnoccupyRoom(button, state):
            PodiumTLP.SetLEDBlinking(65533, 'Slow', ['Off', 'Red'])
        ```
        """
        self._Command('SetLEDBlinking',[ledId, rate, stateList])

    def SetLEDState(self, ledId: int, state: str) -> None:
        """ Drive the LED to the given color

        Arguments:
            - ledId (int) - LED id
            - rate (string) - LED color or ‘Off’.

        Note:
            - Available colors are Red, Green, and Off.

        ---

        Example:
        ```
        @event(SomeOtherButton, 'Released')
        def UnoccupyRoom(button, state):
            PodiumTLP.SetLEDState(65533, 'Off')
        ```
        """
        self._Command('SetLEDState',[ledId, state])

    def SetMotionDecayTime(self, duration: float) -> None:
        """ Set the period of time to trigger MotionDetected after last motion was detected.

        Arguments:
            - duration (float) - time in seconds (minimum/default value is 10)

        ---

        Example:
        ```
        @event(ButtonObject, 'Pressed')
        def Initialize(button, state):
            PodiumTLP.SetMotionDecayTime(30)
        ```
        """
        self._Command('SetMotionDecayTime',[duration])

    def SetMute(self, name: str, mute: str) -> None:
        """ Set the mute state for the given channel

        The defined channel names are:
            - 'Master' - the master volume
            - 'Speaker' - the built-in speakers
            - 'Line' - the line out
            - 'Click' - button click volume
            - 'Sound' - sound track playback volume
            - 'HDMI' - HDMI input volume
            - 'XTP' - XTP input volume

        ---

        Arguments:
            - name (string) - name of channel.
            - mute (string) - mute state ('On' or 'Off')

        ---

        Example:
        ```
        @event(ToggleMute, 'Pressed')
        def toggleMute(button, state):
            if PodiumTLP.GetMute('HDMI') == 'On':
                PodiumTLP.SetMute('HDMI', 'Off')
            else:
                PodiumTLP.SetMute('HDMI', 'On')
        ```
        """
        self._Command('SetMute',[name,mute])

    def SetSleepTimer(self, state, duration: int=None) -> None:
        """ Enable/disable sleep timer. Either 'On' or True enables sleep timer. 'Off' or False disables sleep timer.

        Arguments:
            - state (bool, string) - name of channel.
            - (optional) duration (int) - time in seconds to sleep

        ---

        Example:
        ```
        @event(ButtonObject, 'Pressed')
        def Initialize(button, state):
            PodiumTLP.SetSleepTimer('On', 60)
        ```
        """
        self._Command('SetSleepTimer',[state,duration])

    def SetVolume(self, name: str, level: int) -> None:
        """ Adjust volume level for the given channel

        The defined channel names are:
            - 'Master' - the master volume
            - 'Click' - button click volume
            - 'Sound' - sound track playback volume
            - 'HDMI' - HDMI input volume
            - 'XTP' - XTP input volume

        Arguments:
            - name (string) - name of channel.
            - level (int) - volume level 0 ~ 100
        """
        self._Command('SetVolume',[name,level])

    def SetWakeOnMotion(self, state) -> None:
        """ Enable/disable wake on motion.

        Arguments:
            - state (bool, string) - True ('On') or False (‘Off’) to enable and disable wake on motion, respectively.
        """
        self._Command('SetWakeOnMotion',[state])

    def ShowPage(self, page) -> None:
        """ Show page on the screen

        Arguments:
            - page (int, string) - absolute page number or name
        """
        self._Command('ShowPage',[page])

    def ShowPopup(self, popup, duration: float=0) -> None:
        """ Display pop-up page for a period of time.

        Arguments:
            - page (int, string) - pop-up page number or name
            - (optional) duration (float) - duration the pop-up remains on the screen. 0 means forever.

        Note:
            - If a pop-up is already showing for a finite period of time, calling this method again with the same pop-up will replace the remaining period with the new period.
        """
        self._Command('ShowPopup',[popup,duration])

    def Sleep(self):
        """ Force the device to sleep immediately """
        self._Command('Sleep',[])

    def StopSound(self):
        """ Stop playing sound file """
        self._Command('StopSound',[])

    def Wake(self):
        """ Force the device to wake up immediately """
        self._Command('Wake',[])
