import datetime as _datetime
from extronlib.system.Clock import Clock
from extronlib.system.Email import Email
from extronlib.system.File import File
from extronlib.system.MESet import MESet
from extronlib.system.RFile import RFile
from extronlib.system.Timer import Timer
from extronlib.system.Wait import Wait




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
