from extronlib.engine.IpcpLink import ExtronNode
_debug = False
import traceback

class DanteDomainManager(ExtronNode):
    """ This class provides an interface to Extron Unified Communications solutions.

    Note:
        - System limits 15 DanteDomainManager clients per system.

    ---

    Arguments:
        - Hostname (string)
        - Credentials (tuple)

    Note:
        - Only one object can be instantiated for a given Hostname or IP Address.

    ---

    Parameters:
        - Hostname - Returns (string) - Hostname of the host computer `Note: If unavailable, returns the IP Address.`
        - Credentials

    ---

    Events:
    ---

    Example:
    ```
    from extronlib.software import DanteDomainManager
    ConferencePC = DanteDomainManager('192.168.1.110',('username','password'))
    ```
    """

    _type='DanteDomainManager'
    def __init__(self, Hostname: str, Credentials: tuple=None,ipcp_index=0) -> None:
        """ DanteDomainManager class constructor.

        Arguments:
            - Hostname (string)
            - Credentials (tuple)
        """
        self.Hostname = Hostname
        self.Credentials = Credentials


        self._args = [Hostname,Credentials]
        self._ipcp_index = ipcp_index
        self._alias = f'DDM:{Hostname}'
        self._callback_properties = {}
        self._properties_to_reformat = ['Credentials']
        self._query_properties_init = {}
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


