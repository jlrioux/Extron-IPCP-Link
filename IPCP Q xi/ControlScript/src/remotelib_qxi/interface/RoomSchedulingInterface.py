
from extronlib.interface import RoomSchedulingInterface as ObjectClass
from extronlib.interface import CalendarEvent
from extronlib.system import Timer
from remotelib_qxi.interface.CalendarEvent import ObjectWrapper as CalendarEventWrapper
import json,pickle


#TODO create management of calendar events


class ObjectWrapper(ObjectClass):
    def __str__(self):return(self.alias)
    type = 'RoomSchedulingInterface'
    def __init__(self,p,alias,data):
        self.WrapperBasics = p
        self.alias = alias
        self.args = []
        for arg in data['args']:
            self.args.append(arg)
        self.args = data['args']
        self.initialized = False
        if self.args:
            try:
                ObjectClass.__init__(self,*data['args']) #type:ObjectClass
            except Exception as e:
                print('failed to create {} "{}" with args "{}" with exception: {}'.format(ObjectWrapper.type,self.alias,self.args,str(e)))
                msg='failed to create {} "{}" with args "{}"\nwith exception: {}'.format(self.type,self.alias,self.args,str(e))
                err_msg = {'property':'init','value':self.args,'qualifier':{'code':msg}}
                self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','message':err_msg}))
                return


        """
            WRAPPER CONFIGURATION
        """
        relevant_attrs = ['ActiveEventChanged','CalendarConnected','CalendarConnectedChanged','Connected','Credentials','Disconnected',
                          'Hostname','IPAddress','NextEventChanged','PreviousEventChanged','RoomName','Timezone','TimezoneOffset','TodaysEventsChanged']
        command_attrs = ['CheckIn','Connect','Disconnect','Extend','GetActiveEvent','GetNextEvent','GetPreviousEvent','GetTodaysEvents','Release',
                          'Reserve']
        event_attrs = ['ActiveEventChanged','CalendarConnected','CalendarConnectedChanged','Connected','Disconnected','NextEventChanged','PreviousEventChanged','TodaysEventsChanged']
        self.update_attrs = []
        self.calendar_attrs = ['CheckIn','Extend','ActiveEventChanged','NextEventChanged','PreviousEventChanged','TodaysEventsChanged']

        self.calendar_event_attrs = ['GetBody','Calendar','CheckedIn','End','Location','Organizer','Start','Subject']
        self.calendar_events = {'next':{},'previous':{},'active':{},'today':{}} #type:dict[str,dict[str,CalendarEventWrapper]]

        """
            CONTAINER TO HOLD VALUES OF PROPERTIES OF THE OBJECT
            - properties that do not always exist should have initial values set here then adjusted below
        """
        self.Commands = {}
        for item in relevant_attrs:
            try:
                hasattr(self,item)
            except:
                self.Commands[item] = {'Status': {'Live':None}}
                continue
            if not hasattr(self,item):continue
            attr = getattr(self,item)
            if callable(attr):
                self.Commands[item] = {'Status': {'Live':None}}
            else:
                value = getattr(self,item)
                self.Commands[item] = {'Status': {'Live':value}}
        for item in command_attrs:
            self.Commands[item] = {'Status': {'Live':None}}


        """
            Each event should be defined here and send an update to the remote server with the new value
        """

        for item in event_attrs:
            setattr(self,item,self.create_event_handler(item))


        """
            This timer should update values that don't automatically trigger events when changed.
            Variables defined here store the last known value so an update is sent only when it changes
        """
        self.update_attrs_dict = {}
        for item in self.update_attrs:
            try:
                self.update_attrs_dict[item] = str(getattr(self,item))
            except:
                self.update_attrs_dict[item] = None

        @Timer(1)
        def t(timer,count):
            if self.Commands['Online']['Status']['Live'] == 'Online':
                for item in self.update_attrs:
                    try:
                        attr = getattr(self,item)
                    except:
                        continue
                    if callable(attr):continue
                    if str(attr) != self.update_attrs_dict[item]:
                        self.update_attrs_dict[item] = str(attr)
                        self.Commands[item]['Status']['Live'] = attr
                        update = {'command':item,'value':self.Commands[item]['Status']['Live'],'qualifier':None}
                        self.WrapperBasics.send_message(alias,json.dumps({'type':'update','message':update}))


        #once init is complete, send dump of current values to remote server
        message = {'value':self.Commands}
        self.WrapperBasics.send_message(alias,json.dumps({'type':'init','message':message}))
        self.initialized = True

    def create_event_handler(self,item):
        def e(interface,state):
            def e(interface,state):
                if item not in self.calendar_attrs:
                    self.Commands[item]['Status']['Live'] = state
                    update = {'command':item,'value':self.Commands[item]['Status']['Live'],'qualifier':None}
                    self.WrapperBasics.send_message(self.alias,json.dumps({'type':'update','message':update}))
                else:
                    event_aliases = []
                    if item == 'ActiveEventChanged':type = 'active'
                    elif item == 'NextEventChanged':type = 'next'
                    elif item == 'PreviousEventChanged':type = 'previous'
                    elif item == 'TodaysEventChanged':type = 'today'
                    self.calendar_events[type] = {}
                    for calendar_event in state:
                        event_alias = self.get_calendar_event_alias(calendar_event)
                        self.calendar_events[type][event_alias] = CalendarEventWrapper(self,calendar_event)
                        event_aliases.append(event_alias)
                    update = {'command':item,'value':event_aliases,'qualifier':None}
                    self.WrapperBasics.send_message(self.alias,json.dumps({'type':'update','message':update}))
        return e

    def get_calendar_event_alias(self,calendar_event:'CalendarEventWrapper'):
        return('{}-{}'.format(str(calendar_event.Start),str(calendar_event.Subject)))

    def receive_message(self,data:'dict'):
        if not self.initialized:return
        err_msg = None
        update = None
        if data['property'] in self.calendar_event_attrs:
            alias = data['qualifier']['alias']
            calendar_event = None
            if alias in self.calendar_events['today']:
                calendar_event = self.calendar_events['today'][alias]
            elif alias in self.calendar_events['next']:
                calendar_event = self.calendar_events['next'][alias]
            elif alias in self.calendar_events['previous']:
                calendar_event = self.calendar_events['previous'][alias]
            elif alias in self.calendar_events['active']:
                calendar_event = self.calendar_events['active'][alias]
            else:
                err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'alias':alias,'code':'no such calendar event exists'}}
            if calendar_event:
                if data['type'] == 'command':
                    if hasattr(calendar_event,data['property']):
                        attr = getattr(calendar_event,data['property'])
                        if callable(attr):
                            try:
                                attr(*data['args'])
                            except Exception as e:
                                print('failed to run property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e)))
                                err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'alias':alias,'code':'failed to run property'}}
                        else:
                            try:
                                attr = data['args'][0]
                            except Exception as e:
                                print('failed to set property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e)))
                                err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'alias':alias,'code':'failed to set property'}}
                    else:
                        err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'alias':alias,'code':'property does not exist'}}
                if data['type'] == 'query':
                    value = None
                    if hasattr(calendar_event,data['property']):
                        attr = getattr(calendar_event,data['property'])
                        if callable(attr):
                            try:
                                value = attr(*data['args'])
                                update = {'property':data['property'],'value':value,'qualifier':{'alias':alias}}
                            except Exception as e:
                                print('failed to run property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e)))
                                err_msg = {'property':data['property'],'value':value,'qualifier':{'alias':alias,'code':'failed to set property'}}
                        else:
                            try:
                                value = attr
                                update = {'property':data['property'],'value':value,'qualifier':{'alias':alias}}
                            except Exception as e:
                                print('failed to get property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],alias,data['args'],str(e)))
                                err_msg = {'property':data['property'],'value':value,'qualifier':{'alias':alias,'code':'failed to set property'}}
                    else:
                        err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':'property does not exist'}}
        elif data['type'] == 'command':
            if hasattr(self,data['property']):
                attr = getattr(self,data['property'])
                if callable(attr):
                    try:
                        attr(*data['args'])
                    except Exception as e:
                        msg='failed to run property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e))
                        print(msg)
                        err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':msg}}
                else:
                    try:
                        attr = data['args'][0]
                    except Exception as e:
                        msg='failed to set property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e))
                        print(msg)
                        err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':msg}}
            else:
                err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':'property does not exist'}}
        elif data['type'] == 'query':
            if hasattr(self,data['property']):
                value = None
                attr = getattr(self,data['property'])
                if callable(attr):
                    try:
                        value = attr(*data['args'])
                        update = {'property':data['property'],'value':value,'qualifier':None}
                    except Exception as e:
                        print('failed to run property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e)))
                        err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':'failed to set property'}}
                else:
                    try:
                        value = attr
                        update = {'property':data['property'],'value':value,'qualifier':None}
                    except Exception as e:
                        print('failed to get property "{}" on "{}" with args "{}"\nwith exception: {}'.format(data['property'],self.alias,data['args'],str(e)))
                        err_msg = {'property':data['property'],'value':data['args'],'qualifier':{'code':'failed to set property'}}
            else:
                err_msg = {'property':data['property'],'value':None,'qualifier':{'code':'property does not exist'}}
        if err_msg:
            if 'query id' in data:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','query id':data['query id'],'message':err_msg}))
            else:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'error','message':err_msg}))
        if update:self.WrapperBasics.send_message(self.alias,json.dumps({'type':'query','query id':data['query id'],'message':update}))



    ''' OVERLOADED FUNCTIONS '''
    def Extend(self,duration=None,event=None):
        calendar_event = None #type:CalendarEvent
        if event==None:pass
        elif event in self.calendar_events['today']:
            calendar_event = self.calendar_events['today'][event].calendar_event
        elif event in self.calendar_events['next']:
            calendar_event = self.calendar_events['next'][event].calendar_event
        elif event in self.calendar_events['previous']:
            calendar_event = self.calendar_events['previous'][event].calendar_event
        elif event in self.calendar_events['active']:
            calendar_event = self.calendar_events['active'][event].calendar_event
        return super().Extend(duration,calendar_event)

    def GetActiveEvent(self):
        events = super().GetActiveEvent()
        aliases = []
        for event in events:
            aliases.append(self.get_calendar_event_alias(event))
        return aliases

    def GetNextEvent(self, todayonly = True):
        events = super().GetNextEvent()
        aliases = []
        for event in events:
            aliases.append(self.get_calendar_event_alias(event))
        return aliases

    def GetPreviousEvent(self, todayonly = True):
        events = super().GetNextEvent()
        aliases = []
        for event in events:
            aliases.append(self.get_calendar_event_alias(event))
        return aliases

    def GetTodaysEvents(self, excludeExpired = True):
        events = super().GetTodaysEvents(excludeExpired)
        aliases = []
        for event in events:
            aliases.append(self.get_calendar_event_alias(event))
        return aliases


    def Release(self,event):
        calendar_event = None #type:CalendarEvent
        if event==None:pass
        elif event in self.calendar_events['today']:
            calendar_event = self.calendar_events['today'][event].calendar_event
        elif event in self.calendar_events['next']:
            calendar_event = self.calendar_events['next'][event].calendar_event
        elif event in self.calendar_events['previous']:
            calendar_event = self.calendar_events['previous'][event].calendar_event
        elif event in self.calendar_events['active']:
            calendar_event = self.calendar_events['active'][event].calendar_event
        return super().Release(calendar_event)


    def Reserve(self,start=None,duration=None):
        if start:
            start = pickle.loads(start)
        return super().Reserve(start,duration)

    @property
    def Timezone(self):
        return pickle.dumps(super().Timezone)

    @property
    def TimezoneOffset(self):
        return pickle.dumps(super().TimezoneOffset)