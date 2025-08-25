from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from extronlib.device import UIDevice
from extronlib.engine.IpcpLink import ExtronNode
_debug = False
import traceback


class Button(ExtronNode):
    """ Representation of Hard/Soft buttons

    A button may trigger several events depending on the configuration; however, Touch Panels only issue Pressed and Released messages to the controller. Other events (e.g., Held, Repeated) are timer driven within the Button instance.

    ---

    Arguments:
        - `UIHost` (extronlib.device.UIDevice) - Device object hosting this UIObject
        - `ID` (int,string) - ID or Name of the UIObject
        - (optional) `holdTime` (float) - Time for Held event. Held event is triggered only once if the button is pressed and held beyond this time. If holdTime is given, it must be a floating point number specifying period of time in seconds of button being pressed and held to trigger Held event.
        - (optional) `repeatTime` (float) - Time for Repeated event. After holdTime expires, the Repeated event is triggered for every additional repeatTime of button being held. If repeatTime is given, it must be a floating point number specifying time in seconds of button being held.

    Note: If button is released before holdTime expires, a Tapped event is triggered instead of a Released event. If the button is released after holdTime expires, there will be no Tapped event.

    ---

    Parameters:
        - `BlinkState` - Returns (string) - the current blink state ('Not blinking' or 'Blinking')
        - `Enabled` - Returns (bool) - True if the control object is enabled else False
        - `Host` - Returns (extronlib.device.UIDevice) - UIDevice object that hosts this control object
        - `ID` - Returns (int) - the object ID
        - `Name` - Returns (string) - the object Name
        - `PressedState` - Returns (bool) - True if the button is pressed, else False
        - `State` - Returns (int) - the current visual state number > Note: It does not return the current state if the button is blinking.
        - `Visible` - Returns (bool) - True if the control object is visible else False

    ---

    Events:
        - `Held` - (Event) Get/Set the callback when hold expire event is triggered. The callback function must accept exactly two parameters, which are the Button that triggers the event and the state (e.g. ‘Held’).
        - `Pressed` - (Event) Get/Set the callback when the button is pressed. The callback function must accept exactly two parameters, which are the Button that triggers the event and the state (e.g. ‘Pressed’).
        - `Released` - (Event) Get/Set the callback when the button is released. The callback function must accept exactly two parameters, which are the Button that triggers the event and the state (e.g. ‘Held’).
        - `Repeated` - (Event) Get/Set the callback when repeat event is triggered. The callback function must accept exactly two parameters, which are the Button that triggers the event and the state (e.g. ‘Repeated’).
        - `Tapped` - (Event) Get/Set the callback when tap event is triggered. The callback function must accept exactly two parameters, which are the Button that triggers the event and the state (e.g. ‘Tapped’).
    """

    _type='Button'
    def __init__(self, UIDevice: 'UIDevice', ID: int, holdTime: float=None, repeatTime: float=None,ipcp_index=0) -> None:
        """ Button class constructor.

        Arguments:
            - UIHost (extronlib.device.UIDevice) - Device object hosting this UIObject
            - ID (int,string) - ID or Name of the UIObject
            - (optional) holdTime (float) - Time for Held event. Held event is triggered only once if the button is pressed and held beyond this time. If holdTime is given, it must be a floating point number specifying period of time in seconds of button being pressed and held to trigger Held event.
            - (optional) repeatTime (float) - Time for Repeated event. After holdTime expires, the Repeated event is triggered for every additional repeatTime of button being held. If repeatTime is given, it must be a floating point number specifying time in seconds of button being held.
        """

        #locally stored properties
        self.UIHost = UIDevice
        self.Host = UIDevice #type:UIDevice
        self.ID = ID
        self.holdTime = holdTime
        self.repeatTime = repeatTime
        self._Name = ''
        self._Visible = True
        self._Enabled = True
        self._State = 0
        self._PressedState = False
        self._BlinkState = 'Not blinking'


        #callback properties
        self.Held = None
        self.Pressed = None
        self.Released = None
        self.Repeated = None
        self.Tapped = None

        self._args = [UIDevice.DeviceAlias,ID,holdTime,repeatTime]
        self._ipcp_index = ipcp_index
        self._alias = f'{UIDevice.DeviceAlias}:{ID}'
        self._callback_properties = {'Pressed':None,
                                     'Released':None,
                                     'Repeated':None,
                                     'Tapped':None,
                                     'Held':None}
        self._properties_to_reformat = []
        self._query_properties_init = {'Name':[],
                                         'State':[],
                                         'Enabled':[],
                                         'Visible':[]}
        self._query_properties_always = {'BlinkState':[],
                                         'PressedState':[]}
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
    def BlinkState(self):
        if 'BlinkState' in self._query_properties_init_list:
            self._query_properties_init_list.remove('BlinkState')
            self._BlinkState = self._Query('BlinkState',[])
        if 'BlinkState' not in self._query_properties_always:
            return self._BlinkState
        return self._Query('BlinkState',[])
    @property
    def Enabled(self):
        if 'Enabled' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Enabled')
            self._Enabled = self._Query('BlinkState',[])
        if 'Enabled' not in self._query_properties_always:
            return self._Enabled
        return self._Query('Enabled',[])
    @property
    def Name(self):
        if 'Name' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Name')
            self._Name = self._Query('Name',[])
        if 'Name' not in self._query_properties_always:
            return self._Name
        return self._Query('Name',[])
    @property
    def PressedState(self):
        if 'PressedState' in self._query_properties_init_list:
            self._query_properties_init_list.remove('PressedState')
            self._PressedState = self._Query('PressedState',[])
        if 'PressedState' not in self._query_properties_always:
            return self._PressedState
        return self._Query('PressedState',[])
    @property
    def State(self):
        if 'State' in self._query_properties_init_list:
            self._query_properties_init_list.remove('State')
            self._State = self._Query('State',[])
        if 'State' not in self._query_properties_always:
            return self._State
        return self._Query('State',[])
    @property
    def Visible(self):
        if 'Visible' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Visible')
            self._Visible = self._Query('Visible',[])
        if 'Visible' not in self._query_properties_always:
            return self._Visible
        return self._Query('Visible',[])






    def CustomBlink(self, rate: float, stateList: list) -> None:
        """ Make the button cycle through each of the states provided.

        Arguments:
            - rate (float) - duration of time in seconds for one visual state to stay until replaced by the next visual state.
            - stateList (list of ints) - list of visual states that this button blinks among.
        """
        self._Command('CustomBlink',[rate,stateList])


    def SetBlinking(self, rate: str, stateList: list) -> None:
        """ Make the button cycle, at ADA compliant rates, through each of the states provided.

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

        Note: Using this function will blink in unison with other buttons.

        Arguments:
            - rate (string) - ADA compliant blink rate. ('Slow', 'Medium', 'Fast')
            - stateList (list of ints) - list of visual states that this button blinks among.

        """
        self._Command('SetBlinking',[rate,stateList])

    def SetEnable(self, enable: bool) -> None:
        """ Enable or disable an UI control object.

        Arguments:
            - enable (bool) - True to enable the object or False to disable it.
        """
        if enable not in [True,False]:
            self.__OnError('SetEnable: invalid enable state')
        self._Command('SetEnable',[enable])
        self._Enabled = enable



    def SetState(self, State: int) -> None:
        """ Set the current visual state

        Arguments:
            - State (int) - visual state number

        Note: Setting the current state stops button from blinking, if it is running. (SetBlinking())
        """
        self._Command('SetState',[State])
        self._State = State


    def SetText(self, text: str) -> None:
        """ Specify text to display on the UIObject

        Arguments:
            - text (string) - text to display

        Raises:
            - TypeError
        """
        self._Command('SetText',[text])

    def SetVisible(self, visible: bool) -> None:
        """ Change the visibility of an UI control object.

        Arguments:
            - visible (bool) - True to make the object visible or False to hide it.
        """
        if visible not in [True,False]:
            self.__OnError('SetVisible: invalid visible state')
        self._Command('SetVisible',[visible])
        self._Visible = visible

