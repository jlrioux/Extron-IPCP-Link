"""
To be used alongside server software package extronlib.
Notes:
    extronlib.system.SaveProgramLog
        - can only accept str or None as path parameter.




"""

qxi_flag = True
try:
    import sys,traceback
except:
    qxi_flag = False



_debug = False


from extronlib.interface import EthernetServerInterfaceEx
from extronlib import event
from extronlib.system import Timer,Wait,ProgramLog

import json,queue

class RemoteServer():    #class code

    def __init__(self,wrapper:'WrapperBasics',interface):
        self.__remote_server = None #type:EthernetServerInterfaceEx
        self.__remote_server_buffer = ''
        self.__remote_server = None
        self.__remote_server_password = 'p9oai23jr09p8fmvw98foweivmawthapw4t'
        self.__remote_minimum_client_version = '0.0.0.0'
        self.__remote_server_logged_in = False
        self.__delim = '~!END!~\x0a'
        self.__remote_busy = False
        self.__remote_server_listen_busy = False
        self.__remote_server_error = None
        self.__remote_client_count = 0

        self.interface = interface
        self.alias_list = []

        self.__wrapperbasics = wrapper




        def __fn_debug_server_listen_timer(timer,count):
            if self.__remote_server_listen_busy:return
            self.__remote_server_listen_busy = True
            if self.__remote_server and self.__remote_server_error == None:
                res = self.__remote_server.StartListen()
                if 'Listening' not in res:
                    self.__remote_server_error = res
                    from extronlib.system import ProgramLog
                    ProgramLog('Error Starting Debug Server:{}'.format(res),'info')
                elif 'Already' not in res:
                    ProgramLog('Debug Server restarted:{}'.format(res),'info')
            self.__remote_server_listen_busy = False
        self.__remote_server_listen_timer = Timer(30,__fn_debug_server_listen_timer)
        self.__remote_server_listen_timer.Stop()




    def EnableRemoteServer(self):
        if self.interface == 'AVLAN':port = 11990
        elif self.interface == 'LAN':port = 11991
        else:
            print('unable to start RemoteServer, invalid network interface:{}'.format(self.interface))
            return
        if not self.__remote_server:
            self.__remote_server = EthernetServerInterfaceEx(port,'TCP',Interface=self.interface,MaxClients=5)
            #self.__remote_server_udp = EthernetServerInterfaceEx(port+2,'UDP',Interface=self.interface)
            __remote_res = self.__remote_server.StartListen()
            #__remote_res_udp = self.__remote_server_udp.StartListen()
            self.__remote_server_listen_timer.Restart()
            if __remote_res != 'Listening':
                print('RemoteServer EnableRemoteServer: Failed : {}'.format(__remote_res))
            else:
                print('RemoteServer EnableRemoteServer: Succeeded on port {}'.format(self.interface))
            #if __remote_res_udp != 'Listening':
            #    print('RemoteServer EnableRemoteServer UDP: Failed : {}'.format(__remote_res))
            #else:
            #    print('RemoteServer EnableRemoteServer UDP: Succeeded on port {}'.format(self.interface))

            @event(self.__remote_server, 'ReceiveData')
            def HandheReceiveFromServer_tcp(client,data:'bytes'):
                self.HandheReceiveFromServer(client,data)

            #@event(self.__remote_server_udp, 'ReceiveData')
            #def HandheReceiveFromServer_udp(client,data:'bytes'):
            #    self.HandheReceiveFromServer(client,data)

            @event(self.__remote_server, 'Connected')
            def HandleClientConnect(interface, state):
                self.__remote_client_count = len(self.__remote_server.Clients)
                print('RemoteServer ClientConnect: Client Count : {}'.format(self.__remote_client_count))
                #remove server offline page
                self.__wrapperbasics.set_server_status(interface.IPAddress,'Online')

            @event(self.__remote_server, 'Disconnected')
            def HandleClientDisconnect(interface, state):
                self.__remote_client_count = len(self.__remote_server.Clients)
                print('RemoteServer ClientDisconnect: Client Count : {}'.format(self.__remote_client_count))
                self.__remote_server_logged_in = False
                self.__remote_server_buffer = ''
                #server offline page
                self.__wrapperbasics.set_server_status(interface.IPAddress,'Offline')

    def HandheReceiveFromServer(self,client,data:'bytes'):
        if _debug:print('recieved data:{}'.format(data.decode()))
        self.__remote_server_buffer += data.decode()
        while self.__delim in self.__remote_server_buffer:
            pos = self.__remote_server_buffer.index(self.__delim)
            temp = self.__remote_server_buffer[:pos]
            self.__remote_server_buffer = self.__remote_server_buffer[pos+len(self.__delim):]

            if temp == 'ping()':
                client.Send('pong(){}'.format(self.__delim))
                print('sent pong')
                return
            if self.__remote_server_logged_in and len(temp) > 0:
                self.__wrapperbasics.process_message(temp,client.IPAddress)
            elif self.__remote_server_password in temp:
                self.__remote_server_logged_in = True
                print('RemoteServer HandheReceiveFromServer: Logged In')
    def DisableRemoteServer(self):
        if self.__remote_server:
            self.__remote_server_logged_in = False
            self.__remote_server_listen_timer.Stop()
            self.__remote_server.StopListen()
            for client in self.__remote_server.Clients:
                client.Disconnect()
            self.__remote_server = None
        print('RemoteServer:DisableRemoteServer: Complete')

    def Send(self,message:'str'):
        if self.__remote_server and self.__remote_server_logged_in and not self.__remote_busy:
            for client in self.__remote_server.Clients:
                if _debug:print('sending message to server:{}{}'.format(message,self.__delim))
                try:
                    client.Send('{}{}'.format(message,self.__delim))
                except:
                    pass

    def SetPingBeforeECIConnect(self,value):
        self.__wrapperbasics.SetPingBeforeECIConnect(value)



from remotelib_qxi.device.ProcessorDevice import ObjectWrapper as ProcessorWrapper
from remotelib_qxi.device.SPDevice import ObjectWrapper as SPDWrapper
from remotelib_qxi.device.AdapterDevice import ObjectWrapper as AdapterWrapper
from remotelib_qxi.device.eBUSDevice import ObjectWrapper as EBUSWrapper
from remotelib_qxi.device.UIDevice import ObjectWrapper as UIWrapper

from remotelib_qxi.interface.CircuitBreakerInterface import ObjectWrapper as CircuitBreakerWrapper
from remotelib_qxi.interface.ContactInterface import ObjectWrapper as ContactWrapper
from remotelib_qxi.interface.DanteInterface import ObjectWrapper as DanteWrapper
from remotelib_qxi.interface.DigitalInputInterface import ObjectWrapper as DigitalInputWrapper
from remotelib_qxi.interface.DigitalIOInterface import ObjectWrapper as DigitalIOWrapper
from remotelib_qxi.interface.EthernetClientInterface import ObjectWrapper as EthernetClientWrapper
from remotelib_qxi.interface.EthernetServerInterfaceEx import ObjectWrapper as EthernetServerExWrapper
from remotelib_qxi.interface.FlexIOInterface import ObjectWrapper as FlexIOWrapper
from remotelib_qxi.interface.IRInterface import ObjectWrapper as IRWrapper
from remotelib_qxi.interface.POEInterface import ObjectWrapper as POEWrapper
from remotelib_qxi.interface.RelayInterface import ObjectWrapper as RelayWrapper
from remotelib_qxi.interface.RoomSchedulingInterface import ObjectWrapper as RoomSchedulingWrapper
from remotelib_qxi.interface.SerialInterface import ObjectWrapper as SerialWrapper
from remotelib_qxi.interface.SPInterface import ObjectWrapper as SPWrapper
from remotelib_qxi.interface.SWACReceptacleInterface import ObjectWrapper as SWACReceptacleWrapper
from remotelib_qxi.interface.SWPowerInterface import ObjectWrapper as SWPowerWrapper
from remotelib_qxi.interface.TallyInterface import ObjectWrapper as TallyWrapper
from remotelib_qxi.interface.TemperatureInterface import ObjectWrapper as TemperatureWrapper
from remotelib_qxi.interface.VolumeInterface import ObjectWrapper as VolumeWrapper

from remotelib_qxi.software.DanteDomainManager import ObjectWrapper as DanteDomainManagerWrapper
from remotelib_qxi.software.SummitConnect import ObjectWrapper as SummitConnectWrapper

from remotelib_qxi.system.System import ObjectWrapper as SystemWrapper
from remotelib_qxi.system.RFile import ObjectWrapper as RFileWrapper

from remotelib_qxi.ui.Button import ObjectWrapper as ButtonWrapper
from remotelib_qxi.ui.Knob import ObjectWrapper as KnobWrapper
from remotelib_qxi.ui.Label import ObjectWrapper as LabelWrapper
from remotelib_qxi.ui.Level import ObjectWrapper as LevelWrapper
from remotelib_qxi.ui.Slider import ObjectWrapper as SliderWrapper



class WrapperBasics():
    def log_error(msg):
        ProgramLog(msg,'error')

    __instances = {'AVLAN':None,'LAN':None}
    __remote_servers = {'AVLAN':None,'LAN':None} #type:dict[str,RemoteServer]


    device_types = ['ProcessorDevice','SPDevice','eBUSDevice','UIDevice','AdapterDevice']
    interface_types = ['CircuitBreakerInterface','ContactInterface','DanteInterface','DigitalInputInterface','DigitalIOInterface','EthernetClientInterface','EthernetServerInterfaceEx',
                       'FlexIOInterface','IRInterface','POEInterface','RelayInterface','RoomSchedulingInterface','SerialInterface','SPInterface','SWACReceptacleInterface',
                       'SWPowerInterface','TallyInterface','TemeratureInterface','VolumeInterface']
    software_types = ['DanteDomainManager','SummitConnect']
    system_types = ['System']
    ui_types = ['Button','Knob','Label','Level','Slider']

    constructors = {'ProcessorDevice':ProcessorWrapper,
                'SPDevice':SPDWrapper,
                'eBUSDevice':EBUSWrapper,
                'UIDevice':UIWrapper,
                'AdapterDevice':AdapterWrapper,
                'CircuitBreakerInterface':CircuitBreakerWrapper,
                'ContactInterface':ContactWrapper,
                'DanteInterface':DanteWrapper,
                'DigitalInputInterface':DigitalInputWrapper,
                'DigitalIOInterface':DigitalIOWrapper,
                'EthernetClientInterface':EthernetClientWrapper,
                'EthernetServerInterfaceEx':EthernetServerExWrapper,
                'FlexIOInterface':FlexIOWrapper,
                'IRInterface':IRWrapper,
                'POEInterface':POEWrapper,
                'RelayInterface':RelayWrapper,
                'RoomSchedulingInterface':RoomSchedulingWrapper,
                'SerialInterface':SerialWrapper,
                'SPInterface':SPWrapper,
                'SWACReceptacleInterface':SWACReceptacleWrapper,
                'SWPowerInterface':SWPowerWrapper,
                'TallyInterface':TallyWrapper,
                'TemeratureInterface':TemperatureWrapper,
                'VolumeInterface':VolumeWrapper,
                'DanteDomainManager':DanteDomainManagerWrapper,
                'SummitConnect':SummitConnectWrapper,
                'System':SystemWrapper,
                'RFile':RFileWrapper,
                'Button':ButtonWrapper,
                'Knob':KnobWrapper,
                'Label':LabelWrapper,
                'Level':LevelWrapper,
                'Slider':SliderWrapper}



    wrapped_objects = {'aliases by type':{},
                    'ProcessorDevice':{},
                    'SPDevice':{},
                    'eBUSDevice':{},
                    'UIDevice':{},
                    'AdapterDevice':{},
                    'CircuitBreakerInterface':{},
                    'ContactInterface':{},
                    'DanteInterface':{},
                    'DigitalInputInterface':{},
                    'DigitalIOInterface':{},
                    'EthernetClientInterface':{},
                    'EthernetServerInterfaceEx':{},
                    'FlexIOInterface':{},
                    'IRInterface':{},
                    'POEInterface':{},
                    'RelayInterface':{},
                    'RoomSchedulingInterface':{},
                    'SerialInterface':{},
                    'SPInterface':{},
                    'SWACReceptacleInterface':{},
                    'SWPowerInterface':{},
                    'TallyInterface':{},
                    'TemeratureInterface':{},
                    'VolumeInterface':{},
                    'DanteDomainManager':{},
                    'SummitConnect':{},
                    'System':{},
                    'RFile':{},
                    'Button':{},
                    'Knob':{},
                    'Label':{},
                    'Level':{},
                    'Slider':{}}



    create_objects_queue = queue.Queue()
    objects_queue_busy = False
    def check_create_objects_queue():
        if WrapperBasics.objects_queue_busy:return
        WrapperBasics.objects_queue_busy = True
        while not WrapperBasics.create_objects_queue.empty():
            instance,alias,data,server_ip = WrapperBasics.create_objects_queue.get()
            if _debug:print('creating object:{alias}:{data}'.format(alias=alias,data=data))
            dev = WrapperBasics.constructors[data['device type']](instance,alias,data)
            dev._server_ip = server_ip
            if dev.initialized:
                pass#WrapperBasics.register(data['device type'],alias,dev)
            else:
                print('failed to create object:{alias}:{data}'.format(alias=alias,data=data))
        WrapperBasics.objects_queue_busy = False

    def SetPingBeforeECIConnect(self,value):
        vals = {True:True,False:False,None:None,
                'Enable':True,'Disable':False,'Auto':None}
        self._ping_before_eci_connect = vals[value]

    def process_message(self,data,ipaddress):
        @Wait(0)
        def w():
            self.receive_message(data,ipaddress)




    def register(self,type,alias,obj):
        if alias in WrapperBasics.wrapped_objects['aliases by type']:return
        if type in WrapperBasics.wrapped_objects:
            WrapperBasics.wrapped_objects[type][alias] = obj
            WrapperBasics.wrapped_objects['aliases by type'][alias] = type
            if _debug:print('registered {} "{}"'.format(type,alias))


    def __init__(self,interface):
        WrapperBasics.__instances[interface] = self
        self.remote_server = RemoteServer(self,interface)
        WrapperBasics.__remote_servers[interface] = self.remote_server
        self._ping_before_eci_connect = None


    '''
    message: str
        format: alias~~data
            data is a json string
                data can be in 3 forms
                    1. {'type':'init','device type':str,'args':list}
                    2. {'type':'query','property':str,'args':list}
                    3. {'type':'command','property':str,'args':list}} #item 0 is value
                queries should be used when expecting a response
                commands should be used when not expecting a response
    '''
    def receive_message(self,message,server_ip):
        if len(message) == 0:return
        try:
            alias,message = message.split('~~')
        except:
            print('~~~ error decoding message received on split:{message}'.format(message=message))

        type = None
        try:
            data = json.loads(message)
        except Exception as e:
            print('failed to decode json message from remote server:{}'.format(str(e)))
            return
        if alias not in self.remote_server.alias_list:
            if _debug:print('~~~NEW ALIAS ADD TO LIST:{alias}'.format(alias=alias))
            self.remote_server.alias_list.append(alias)
        if alias in WrapperBasics.wrapped_objects['aliases by type']:
            type = WrapperBasics.wrapped_objects['aliases by type'][alias]
            if alias in WrapperBasics.wrapped_objects[type]:
                WrapperBasics.wrapped_objects[type][alias].receive_message(data)
                return
            else:
                ProgramLog('Alias not associated with an object:{alias}'.format(alias=alias),Severity='warning')
        else:
            if _debug:print('~~~NEW DEVICE:{alias}'.format(alias=alias))
            """
            if this message isn't the details needed to create the object, send a request for the details, then return.
            if this is a create message, create the object and register it
            """
            if data['type'] == 'init':
                #print('init device:{alias}'.format(alias=alias))
                #create the device and register it
                WrapperBasics.create_objects_queue.put([self,alias,data,server_ip])
                WrapperBasics.check_create_objects_queue()
                return
        if not type:
            err_msg = {'property':'init','value':'device does not exist','qualifier':{'alias':alias,'code':'missing device'}}
            self.send_message(alias,json.dumps({'type':'error','message':err_msg}))
            WrapperBasics.log_error('remotelib error:{}:{}'.format(alias,json.dumps(err_msg)))

    def send_message(self,alias,data):
        message = '{}~~{}'.format(alias,data)
        for interface in WrapperBasics.__remote_servers:
            if interface:
                server = WrapperBasics.__remote_servers[interface]
                if server:
                    if alias in server.alias_list:
                        if _debug:print('sending message:{}'.format(message))
                        server.Send(message)

    def set_server_status(self,ip,status):
        #get list of panels for this host ip
        panels = []
        for alias in WrapperBasics.wrapped_objects['UIDevice']:
            dev = WrapperBasics.wrapped_objects['UIDevice'][alias]
            if dev._server_ip == ip:
                panels.append(dev)
        if status == 'Online':
            for panel in panels:panel.HidePopup('Control Server is Offline')
        elif status == 'Offline':
            for panel in panels:panel.ShowPopup('Control Server is Offline')















