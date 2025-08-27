import datetime as _datetime
from extronlib.system.Clock import Clock
from extronlib.system.Email import Email
from extronlib.system.File import File
from extronlib.system.MESet import MESet
from extronlib.system.RFile import RFile
from extronlib.system.Timer import Timer
from extronlib.system.Wait import Wait

from extronlib.engine.IpcpLink import ExtronNode
import traceback
import datetime,base64,pickle
_debug = False


# ------ SSL METHODS --------
def GetUnverifiedContext(ipcp_index=0) -> None:
    """ Python 3.4.3 changed the default behavior of the stdlib http clients. They will now verify that “the server presents a certificate which is signed by a
    CA in the platform trust store and whose hostname matches the hostname being requested by default”. This method returns an unverified context for use when
    a valid certificate is impossible.

    Returns:
        - context (ssl.SSLContext) - unverified context object compatible with stdlib http clients.

    Warning:
        This is a potential security risk. It should only be used when a secure solution is impossible. GetSSLContext should be used whenever possible.
    """
    from extronlib.engine.IpcpLink import IpcpLink as _Links
    return _Links.ipcp_links[ipcp_index].System.GetUnverifiedContext()



def GetSSLContext(alias,ipcp_index=0) -> None:
    """ Retrieve a Certificate Authority certificate from the Security Store and use it to create an SSL context usable with standard Python http clients.

    Parameters:
        alias (string) - name of the CA certificate as it appears in the Security Store.

    Returns:
        - context (ssl.SSLContext) - an SSL context object compatible with stdlib http clients.

    example:
        import urllib.request
        from extronlib.system import GetSSLContext

        context = GetSSLContext('yourcert')

        urllib.request.urlopen("https://www.example.com", context=context)
    """
    from extronlib.engine.IpcpLink import IpcpLink as _Links
    return _Links.ipcp_links[ipcp_index].System.GetSSLContext(alias)




# ------ TIME METHODS --------
def SetAutomaticTime(Server: str,ipcp_index=0) -> None:
    """ Turn on NTP time synchronization using Server as the time source.

    Arguments:
        - Server (string) – the NTP server to synchronize with
    """
    from extronlib.engine.IpcpLink import IpcpLink as _Links
    _Links.ipcp_links[ipcp_index].System.SetAutomaticTime(Server)



def SetManualTime(DateAndTime: _datetime,ipcp_index=0) -> None:
    """ Change the system time. This will turn off NTP synchronization if it is on.

    Arguments:
        - Server (string) – the NTP server to synchronize with
    """
    from extronlib.engine.IpcpLink import IpcpLink as _Links
    _Links.ipcp_links[ipcp_index].System.SetManualTime(DateAndTime)



def GetCurrentTimezone(ipcp_index=0) -> tuple:
    """ The returned namedtuple contains three pieces of string data: the time zone id, the time zone description, and MSid which contains a Microsoft-compatible time zone identifier

    Returns:
        - namedtuple (tuple) – the current time zone of the primary controller
    """
    from extronlib.engine.IpcpLink import IpcpLink as _Links
    return _Links.ipcp_links[ipcp_index].System.GetCurrentTimezone()


def GetTimezoneList(ipcp_index=0) -> list:
    """ Each item in the returned list is a namedtuple that contains three pieces of string data: the time zone id, the time zone description, and MSid which contains a Microsoft-compatible time zone identifier.

    Returns:
        - listof namedtuples (list) – all time zones supported by the system
    """
    from extronlib.engine.IpcpLink import IpcpLink as _Links
    return _Links.ipcp_links[ipcp_index].System.GetTimezoneList()



def SetTimeZone(id,ipcp_index=0) -> None:
    """ Change the system time zone. Time zone affects Daylight Saving Time behavior and is used to calculate time of day when NTP time synchronization is turned on.

    Arguments:
        - id (string) –  The new system time zone identifier. Use an item returned by GetTimezoneList to get the time zone id for this parameter.
    """
    from extronlib.engine.IpcpLink import IpcpLink as _Links
    _Links.ipcp_links[ipcp_index].System.SetTimeZone(id)




# ------ NETWORK METHODS --------
def WakeOnLan(macAddress: str, port=9,ipcp_index=0) -> None:
    """ Wake-on-LAN is an computer networking standard that allows a computer to be awakened by a network message. The network message, ‘Magic Packet’, is sent out through UDP broadcast, port 9.

    Arguments:
        - macAddress (string) - Target device’s MAC address. The format is six groups of two hex digits, separated by hyphens ('01-23-45-67-ab-cd', e.g.).
        - (optional) port (int) - Port on which target device is listening.

    Note: Typical ports for WakeOnLan are 0, 7 and 9.
    """
    from extronlib.engine.IpcpLink import IpcpLink as _Links
    _Links.ipcp_links[ipcp_index].System.WakeOnLan(macAddress,port)



def Ping(hostname='localhost', count=5,ipcp_index=0) -> tuple:
    """ Ping a host and return the result in a tuple: (# of success ping, # of failure ping , avg time)

    Arguments:
        - (optional) hostname (string) - IP address to ping.
        - (optional) count (int) - how many times to ping.

    Returns
        - tuple (# of success, # of fail, avg time ) (int, int, float)
    """
    from extronlib.engine.IpcpLink import IpcpLink as _Links
    return _Links.ipcp_links[ipcp_index].System.Ping(hostname,count)




# ------ OTHER METHODS --------
def GetSystemUpTime(ipcp_index=0) -> int:
    """ Returns system up time in seconds.

    Returns
        - system up time in seconds (int)
    """
    from extronlib.engine.IpcpLink import IpcpLink as _Links
    return _Links.ipcp_links[ipcp_index].System.GetSystemUpTime()


def ProgramLog(Entry: str, Severity='error',ipcp_index=0) -> None:
    """ Write entry to program log file.

    Arguments:
        - Entry (string) - the message to enter into the log
        - (optional) Severity (string) - indicates the severity to the log viewer. ('info', 'warning', or 'error')
    """
    from extronlib.engine.IpcpLink import IpcpLink as _Links
    _Links.ipcp_links[ipcp_index].System.ProgramLog(Entry,Severity)


def SaveProgramLog(path:'File|str'=None,ipcp_index=0) -> None:
    """ Write program log to file.

    Arguments:
        - Entry (string) - the message to enter into the log
        - (optional) Severity (string) - indicates the severity to the log viewer. ('info', 'warning', or 'error')
    """
    from extronlib.engine.IpcpLink import IpcpLink as _Links
    if type(path) == File:
        path = path.Filename
    _Links.ipcp_links[ipcp_index].System.SaveProgramLog(path)





class System(ExtronNode):
    """ Class to send System using the configured mail settings. The confiured settings can be over ridden during instantiation.

    Note: default sender will be login username@unit-name or hostname@unit-name if there is no authentication. To override, call Sender()

    ---

    Arguments:
        - smtpServer (string) - ip address or hostname of SMTP server
        - port (int) - port number
        - username (string) - login username for SMTP authentication
        - password (string) - login password for SMTP authentication
        - sslEnabled (bool) - Enable (True) or Disable (False) SSL for the connection
    """

    _type='System'
    def __init__(self,ipcp_index=0):
        """ System class constructor.

        """
        self._args = []
        self._ipcp_index = ipcp_index
        self._alias = f'System'
        self._callback_properties = []
        self._properties_to_reformat = []
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



    def GetUnverifiedContext(self) -> None:
        """ Python 3.4.3 changed the default behavior of the stdlib http clients. They will now verify that “the server presents a certificate which is signed by a
        CA in the platform trust store and whose hostname matches the hostname being requested by default”. This method returns an unverified context for use when
        a valid certificate is impossible.

        Returns:
            - context (ssl.SSLContext) - unverified context object compatible with stdlib http clients.

        Warning:
            This is a potential security risk. It should only be used when a secure solution is impossible. GetSSLContext should be used whenever possible.
        """
        import ssl
        context = ssl._create_unverified_context()
        return context






    def GetSSLContext(self,alias) -> None:
        """ this actually fakes it.  This will need to be dumped on the server, not the IPCP controller, in the SSL Certificates folder"""
        """ Retrieve a Certificate Authority certificate from the Security Store and use it to create an SSL context usable with standard Python http clients.

        Parameters:
            alias (string) - name of the CA certificate file.

        Returns:
            - context (ssl.SSLContext) - an SSL context object compatible with stdlib http clients.

        example:
            import urllib.request
            from extronlib.system import GetSSLContext

            context = GetSSLContext('yourcert')

            urllib.request.urlopen("https://www.example.com", context=context)
        """
        import ssl,os
        __cwd = '{}{}'.format(os.getcwd(),'//extronlib//engine//SSL Certificates//')
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.load_verify_locations(capath=f'{__cwd}{alias}')
        return context





    # ------ TIME METHODS --------
    def SetAutomaticTime(self,Server: str) -> None:
        """ Turn on NTP time synchronization using Server as the time source.

        Arguments:
            - Server (string) – the NTP server to synchronize with
        """
        self._Command('SetAutomaticTime',[Server])


    def SetManualTime(self,DateAndTime: datetime) -> None:
        """ Change the system time. This will turn off NTP synchronization if it is on.

        Arguments:
            - Server (string) – the NTP server to synchronize with
        """
        self._Command('SetManualTime',[base64.b64encode(pickle.dumps(DateAndTime)).decode('utf-8')])


    def GetCurrentTimezone(self) -> tuple:
        """ The returned namedtuple contains three pieces of string data: the time zone id, the time zone description, and MSid which contains a Microsoft-compatible time zone identifier

        Returns:
            - namedtuple (tuple) – the current time zone of the primary controller
        """
        try:
            val = pickle.loads(base64.b64decode(self._Query('GetCurrentTimezone',[])))
        except:
            val = None
        return val


    def GetTimezoneList(self) -> list:
        """ Each item in the returned list is a namedtuple that contains three pieces of string data: the time zone id, the time zone description, and MSid which contains a Microsoft-compatible time zone identifier.

        Returns:
            - listof namedtuples (list) – all time zones supported by the system
        """
        try:
            val = pickle.loads(base64.b64decode(self._Query('GetTimezoneList',[])))
        except:
            val = None
        return val



    def SetTimeZone(self,id) -> None:
        """ Change the system time zone. Time zone affects Daylight Saving Time behavior and is used to calculate time of day when NTP time synchronization is turned on.

        Arguments:
            - id (string) –  The new system time zone identifier. Use an item returned by GetTimezoneList to get the time zone id for this parameter.
        """
        self._Command('SetTimeZone',[id])




    # ------ NETWORK METHODS --------
    def WakeOnLan(self,macAddress: str, port=9) -> None:
        """ Wake-on-LAN is an computer networking standard that allows a computer to be awakened by a network message. The network message, ‘Magic Packet’, is sent out through UDP broadcast, port 9.

        Arguments:
            - macAddress (string) - Target device’s MAC address. The format is six groups of two hex digits, separated by hyphens ('01-23-45-67-ab-cd', e.g.).
            - (optional) port (int) - Port on which target device is listening.

        Note: Typical ports for WakeOnLan are 0, 7 and 9.
        """
        self._Command('WakeOnLan',[macAddress,port])

    def Ping(self,hostname='localhost', count=5) -> tuple:
        """ Ping a host and return the result in a tuple: (# of success ping, # of failure ping , avg time)

        Arguments:
            - (optional) hostname (string) - IP address to ping.
            - (optional) count (int) - how many times to ping.

        Returns
            - tuple (# of success, # of fail, avg time ) (int, int, float)
        """
        try:
            val = pickle.loads(base64.b64decode(self._Query('Ping',[hostname,count])))
        except:
            val = None
        return val


    # ------ OTHER METHODS --------
    def GetSystemUpTime(self) -> int:
        """ Returns system up time in seconds.

        Returns
            - system up time in seconds (int)
        """
        return self._Query('GetSystemUpTime',[])

    def ProgramLog(self,Entry: str, Severity='error') -> None:
        """ Write entry to program log file.

        Arguments:
            - Entry (string) - the message to enter into the log
            - (optional) Severity (string) - indicates the severity to the log viewer. ('info', 'warning', or 'error')
        """
        self._Command('ProgramLog',[Entry,Severity])

    def SaveProgramLog(self,path=None) -> None:
        """ Write program log to file.

        Arguments:
            - Entry (string) - the message to enter into the log
            - (optional) Severity (string) - indicates the severity to the log viewer. ('info', 'warning', or 'error')
        """
        from extronlib.system import File
        if path == None:
            path = 'ProgramLog {}.txt'.format(datetime.now().strftime('%Y-%m-%d %H%M%S'))
        log = self._Query('SaveProgramLog',[path])
        #write log to file
        if File.Exists(path):
            mode = 'w'
        else:
            mode = 'x'
        f = File(path,mode)
        if f:
            f.write(log)
