from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from extronlib.device import UIDevice
from extronlib.engine.IpcpLink import ExtronNode
from extronlib.system import Wait
_debug = False
import traceback

class Slider(ExtronNode):
    """ This module defines interfaces of Slider UI.

    ---

    Arguments:
        - UIHost (extronlib.device.UIDevice) - Device object hosting this UIObject
        - ID (int) - ID of the UIObject

    ---

    Parameters:
        - Host - Returns (extronlib.device.UIDevice) - UIDevice object that hosts this control object
        - ID - Returns (int) - the object ID
        - Fill - Returns (int) - the current fill level
        - Max - Returns (int) - the upper bound of the slider object
        - Min - Returns (int) - the lower bound of the slider object
        - Name - Returns (string) - the object Name
        - Visible - Returns (bool) - True if the control object is visible else False
        - Step - Returns (int, float)	- the step size of the slider object
        - Enabled - Returns (bool) - True if the control object is enabled else False


    Events:
        - Changed - (Event) Triggers when the slider value is changed by user interaction (i.e. after Pressed but before Released).
          -- The callback takes three arguments. The first is the Slider instance triggering the event, the second is the state, and the third is the new slider value.
        - Pressed - (Event) Triggers when the slider is pressed. The callback takes three arguments. The first is the Slider instance triggering the event, the second is the state, and the third is the new slider value
        - Released - (Event) Triggers when the slider is released. The callback takes three arguments. The first is the Slider instance triggering the event, the second is the state, and the third is the new slider value.
    """

    _type='Slider'
    def __init__(self, UIDevice:'UIDevice', ID: int,ipcp_index=0) -> None:
        """ Level class constructor.

        Arguments:
            - UIHost (extronlib.device.UIDevice) - Device object hosting this UIObject
            - ID (int) - ID of the UIObject
        """
        self.UIHost = UIDevice
        self.ID = ID
        self._Name = ''
        self._Visible = True
        self._Enabled = True
        self._Max = 100
        self._Min = 0
        self._Step = 1
        self._Fill = 0


        self.Pressed = None
        self.Released = None
        self.Changed = None


        self._args = [UIDevice.DeviceAlias,ID]
        self._ipcp_index = ipcp_index
        self._alias = f'{UIDevice.DeviceAlias}:{ID}'
        self._callback_properties = {'Pressed':None,
                                     'Released':None,
                                     'Changed':{'var':'_Fill','value index':1}}
        self._properties_to_reformat = []
        self._query_properties_init = {'Name':[],
                                    'Fill':[],
                                    'Visible':[],
                                    'Max':[],
                                    'Min':[],
                                    'Step':[],
                                    'Enabled':[]}
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
    def Name(self):
        if 'Name' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Name')
            self._Name = self._Query('Name',[])
        if 'Name' not in self._query_properties_always:
            return self._Name
        return self._Query('Name',[])
    @property
    def Max(self):
        if 'Max' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Max')
            self._Max = self._Query('Max',[])
        if 'Max' not in self._query_properties_always:
            return self._Max
        return self._Query('Max',[])
    @property
    def Min(self):
        if 'Min' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Min')
            self._Min = self._Query('Min',[])
        if 'Min' not in self._query_properties_always:
            return self._Min
        return self._Query('Min',[])
    @property
    def Visible(self):
        if 'Visible' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Visible')
            self._Visible = self._Query('Visible',[])
        if 'Visible' not in self._query_properties_always:
            return self._Visible
        return self._Query('Visible',[])
    @property
    def Step(self):
        if 'Step' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Step')
            self._Step = self._Query('Step',[])
        if 'Step' not in self._query_properties_always:
            return self._Step
        return self._Query('Step',[])
    @property
    def Fill(self):
        if 'Fill' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Fill')
            self._Fill = self._Query('Fill',[])
        if 'Fill' not in self._query_properties_always:
            return self._Fill
        return self._Query('Fill',[])
    @property
    def Enabled(self):
        if 'Enabled' in self._query_properties_init_list:
            self._query_properties_init_list.remove('Enabled')
            self._Enabled = self._Query('Enabled',[])
        if 'Enabled' not in self._query_properties_always:
            return self._Enabled
        return self._Query('Enabled',[])



    def Dec(self) -> None:
        """ Nudge the level down a step """
        if self._Fill-self._Step >= self._Min:
            self._Fill -= self._Step
        else:
            self._Fill = self._Min
        self._Command('Dec',[])


    def Inc(self) -> None:
        """ Nudge the level up a step """
        if self._Fill+self._Step >= self._Max:
            self._Fill += self._Step
        else:
            self._Fill = self._Max
        self._Command('Inc',[])

    def SetFill(self, Fill: int) -> None:
        """ Set the current fill level

        Arguments:
            - Fill (int) - Discrete value of the level object. The default range is 0 - 100 with a step size of 1.
        """
        if self._Min <= Fill <= self._Max:
            self._Fill = Fill
            self._Command('SetFill',[Fill])
        else:
            self.__OnError('SetFill: Value out of range')




    def SetRange(self, Min: int, Max: int, Step: int=1) -> None:
        """ Set level object’s allowed range and the step size

        Arguments:
            - Min (int) - Minimum level
            - Max (int) - Maximum level
            - (optional) Step (int) - Optional step size for Inc() and Dec().
        """
        self._Min = Min
        self._Max = Max
        self._Step = Step
        self._Command('SetRange',[Min,Max,Step])
        self._Fill = self._Query('Fill',[])





    def SetVisible(self, visible: bool) -> None:
        """ Change the visibility of an UI control object.

        Arguments:
            - visible (bool) - True to make the object visible or False to hide it.
        """
        if visible not in [True,False]:
            self.__OnError('SetVisible: invalid enable state')
        self._Command('SetVisible',[visible])
        self._Visible = visible




    def SetEnable(self, enable: bool) -> None:
        """ Change the visibility of an UI control object.

        Arguments:
            - visible (bool) - True to make the object visible or False to hide it.
        """
        if enable not in [True,False]:
            self.__OnError('SetEnable: invalid enable state')
        self._Command('SetEnable',[enable])
        self._Enabled = enable