from extronlib.engine.IpcpLink import ExtronNode
_debug = False
import traceback

class ProcessorDevice(ExtronNode):
    def __str__(self):return(self.DeviceAlias)
    """ Defines common interface to Extron Control Processors

    Note:
        - `DeviceAlias` must be a valid device Device Alias of an Extron device in the system.
        - If the part number is provided, the device will trigger a warning message in the program log if it does not match the connected device.

    ---

    Functions:
        - Reboot: Performs a soft restart of this device – this is equivalent to rebooting a PC.
        - SetExecutiveMode: Sets the desired Executive Mode

    ---

    Arguments:
        - DeviceAlias (string) - Device Alias of the Extron device
        - (optional) PartNumber  (string) - device’s part number

    ---

    Parameters:
        - CurrentLoad - Returns (float) - the current load of 12V DC power supply. This only applies to ProcessorDevice featuring 12V DC power supply. It returns None otherwise.
        - DeviceAlias - Returns (string) - the device alias of the object
        - ExecutiveMode - Returns (int) - The current executive mode number.
        - FirmwareVersion - Returns (string) - the firmware version of this device
        - Hostname - Returns (string) - the hostname of this device
        - IPAddress - Returns (string) - IP address of this device
        - LinkLicenses - Returns (list of strings) - List of LinkLicense® part numbers.
        - MACAddress - Returns (string) - MAC address of this device. For dual NIC devices, the LAN address is returned.
        - ModelName - Returns (string) - Model name of this device
        - PartNumber - Returns (string) - the part number of this device
        - SerialNumber - Returns (string) - Serial number of this device
        - UserUsage - Returns (tuple of ints) - user data usage of this device in KB (used, total).

    ---

    Events:
        - ExecutiveModeChanged - (Event) Triggers when executive mode changes. The callback takes two arguments. The first one is the extronlib.device instance triggering the event and the second one is is the executive mode number.
        - Offline - (Event) Triggers when the device goes offline. The callback takes two arguments. The first one is the extronlib.device instance triggering the event and the second one is a string ('Offline').
        - Online - (Event) Triggers when the device comes online. The callback takes two arguments. The first one is the extronlib.device instance triggering the event and the second one is a string ('Online').

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

    _type='ProcessorDevice'
    def __init__(self, DeviceAlias: str, PartNumber: str=None,ipcp_index=0):
        """
        ProcessorDevice class constructor.

        Arguments:
            - DeviceAlias (string) - Device Alias of the Extron device
            - PartNumber  (string) - device’s part number
        """

        self._CurrentLoad = None
        """	Float : the current load of 12V DC power supply in watts

        Note:
            - This only applies to ProcessorDevice featuring 12V DC power supply. It returns None otherwise.
        """

        self._CombinedCurrent = None
        self.CombinedCurrentChanged = None
        self._CombinedLoadState = None
        self.CombinedLoadStateChanged = None
        self._CombinedWattage = None
        self.CombinedWattageChanged = None


        self.DeviceAlias = DeviceAlias
        self._ExecutiveMode = None
        self.ExecutiveModeChanged = None
        """Event: Triggers when executive mode changes.

        The callback takes two arguments. The first is the extronlib.device instance triggering the event and the second is the executive mode number.

        ---

        Example:
        ```
        @event(proc, 'ExecutiveModeChanged')
        def HandleExecutiveMode(device, ExecutiveMode):
            -    print('Executive mode changed to {}.'.format(ExecutiveMode))
        ```
        """
        self._FirmwareVersion = ''
        self._Hostname = ''
        self._IPAddress = ''
        """Note:
            - For control processors with AV LAN, the LAN address is returned."""
        self._LinkLicenses = []
        """	List of LinkLicense® part numbers."""
        self._MACAddress = ''
        """
        Note:
            - For control processors with AV LAN, the LAN address is returned.
        """
        self._ModelName = ''
        self.Offline = None
        """
        Event:
            -    Triggers when the device goes offline.

        The callback takes two arguments. The first one is the extronlib.device instance triggering the event and the second one is a string ('Offline').
        """
        self.Online = None
        """
        Event:
            -    Triggers when the device goes online.

        The callback takes two arguments. The first one is the extronlib.device instance triggering the event and the second one is a string ('Online').
        """
        self._PartNumber = ''
        self._SerialNumber = ''
        self._UserUsage = ()
        """user data usage of this device in KB (used, total)."""
        self._SystemSettings = {}
        """
        Returns:
            -    dict: a dictionary of data describing the settings (defined in Toolbelt) of this device

        ---

        Example:
        ```
        {
            'Network': {
                'LAN': [
                    'DNSServers': ['192.168.1.1',],
                    'Gateway': '192.168.254.1',
                    'Hostname': 'ConfRoom',
                    'IPAddress': '192.168.254.250',
                    'SubnetMask': '255.255.255.0',
                    'SearchDomains': ['extron.com',],
                ],
                'AVLAN': [
                    'DHCPServer': 'Off',
                    'DNSServers': ['192.168.1.1',],
                    'Hostname': 'ConfRoom',
                    'IPAddress': '192.168.253.251',
                    'SubnetMask': '255.255.255.0',
                    'SearchDomains': ['extron.com',],
                ],
            },
            'MailServer': {
                'IPAddress': '192.168.254.100',
                'SMTPPort': 25,
                'SSLEnabled': True,
                'UserID': 'jdoe',
            },
            'DateTime': {
                'NTPSettings': {
                    'Enabled': True,
                    'Server': '192.168.254.101',    # '' if Enable == False
                },
                'TimeZone': '(UTC-08:00/UTC-07:00) Pacific Time',
            }
            'ProgramInformation': {
                'Author': 'jdoe',
                'DeviceName': 'IPCP Pro 550 : 192.168.254.250',
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
        self._callback_properties = {'CombinedWattageChanged':{'var':'_CombinedWattage','value index':1},
                                     'CombinedCurrentChanged':{'var':'_CombinedCurrent','value index':1},
                                     'CombinedLoadStateChanged':{'var':'_CombinedCurrent','value index':1},
                                     'ExecutiveModeChanged':{'var':'_ExecutiveMode','value index':1},
                                     'Offline':None,
                                     'Online':None}
        self._properties_to_reformat = ['UserUsage']
        self._query_properties_init = {}
        self._query_properties_always = {'DeviceAlias':[],
                                         'CurrentLoadd':[],
                                         'CombinedCurrent':[],
                                         'CombinedLoadState':[],
                                         'CombinedWattage':[],
                                         'ExecutiveMode':[],
                                         'FirmwareVersion':[],
                                         'Hostname':[],
                                         'IPAddress':[],
                                         'LinkLicenses':[],
                                         'MACAddress':[],
                                         'ModelName':[],
                                         'PartNumber':[],
                                         'SerialNumber':[],
                                         'UserUsage':[],
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
    def CurrentLoad(self):
        if 'CurrentLoad' in self._query_properties_init_list:
            self._query_properties_init_list.remove('CurrentLoad')
            self._CurrentLoad = self._Query('CurrentLoad',[])
        if 'CurrentLoad' not in self._query_properties_always:
            return self._CurrentLoad
        return self._Query('CurrentLoad',[])
    @property
    def CombinedCurrent(self):
        if 'CombinedCurrent' in self._query_properties_init_list:
            self._query_properties_init_list.remove('CombinedCurrent')
            self._CombinedCurrent = self._Query('CombinedCurrent',[])
        if 'CombinedCurrent' not in self._query_properties_always:
            return self._CombinedCurrent
        return self._Query('CombinedCurrent',[])
    @property
    def CombinedLoadState(self):
        if 'CombinedLoadState' in self._query_properties_init_list:
            self._query_properties_init_list.remove('CombinedLoadState')
            self._CombinedLoadState = self._Query('CombinedLoadState',[])
        if 'CombinedLoadState' not in self._query_properties_always:
            return self._CombinedLoadState
        return self._Query('CombinedLoadState',[])
    @property
    def CombinedWattage(self):
        if 'CombinedWattage' in self._query_properties_init_list:
            self._query_properties_init_list.remove('CombinedWattage')
            self._CombinedWattage = self._Query('CombinedWattage',[])
        if 'CombinedWattage' not in self._query_properties_always:
            return self._CombinedWattage
        return self._Query('CombinedWattage',[])
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
    def UserUsage(self):
        if 'UserUsage' in self._query_properties_init_list:
            self._query_properties_init_list.remove('UserUsage')
            self._UserUsage = self._Query('UserUsage',[])
        if 'UserUsage' not in self._query_properties_always:
            return self._UserUsage
        return self._Query('UserUsage',[])
    @property
    def SystemSettings(self):
        if 'SystemSettings' in self._query_properties_init_list:
            self._query_properties_init_list.remove('SystemSettings')
            self._SystemSettings = self._Query('SystemSettings',[])
        if 'SystemSettings' not in self._query_properties_always:
            return self._SystemSettings
        return self._Query('SystemSettings',[])


    def Reboot(self) -> None:
        """Performs a soft restart of this device – this is equivalent to rebooting a PC.

        ---

        ### WARNING
            -    Any unsaved data will be lost, including Program Log. Follow the example below.

        ---

        Example:
        ```
        from extronlib.system import File, SaveProgramLog
        from datetime import datetime

        # Save the ProgramLog for later inspection.
        dt = datetime.now()
        filename = 'ProgramLog {}.txt'.format(dt.strftime('%Y-%m-%d %H%M%S'))

        with File(filename, 'w') as f:
            -    SaveProgramLog(f)

        device.Reboot()
        ```
        """
        self._Command('Reboot',[])

    def SetExecutiveMode(self, ExecutiveMode: int) -> float:
        """ Sets the desired Executive Mode.

        ---

        Note:
            - See product manual for list of available modes.

        ---

        Arguments:
            - ExecutiveMode (int) - The mode to set. 0 to n.
        """
        self._Command('SetExecutiveMode',[ExecutiveMode])
