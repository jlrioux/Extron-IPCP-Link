
from extronlib.interface import CalendarEvent as ObjectClass
import pickle

class ObjectWrapper():
    type = 'CalendarEvent'
    def __init__(self,parent,event:'ObjectClass'):
        self.initialized = False
        self.alias = self.get_calendar_event_alias(event)
        self.parent = parent
        self.calendar_event = event

        """
            WRAPPER CONFIGURATION
        """
        relevant_attrs = ['GetBody','Calendar','CheckedIn','End','Location','Organizer','Start','Subject']

        self.initialized = True

    def get_calendar_event_alias(self,calendar_event:'ObjectClass'):
        return('{}-{}'.format(str(calendar_event.Start),str(calendar_event.Subject)))

    def GetBody(self,html=False):
        return self.calendar_event.GetBody(html)

    @property
    def Calendar(self):
        return self.parent.alias

    @property
    def CheckedIn(self):
        return self.calendar_event.CheckedIn()

    @property
    def End(self):
        return pickle.dumps(self.calendar_event.End())

    @property
    def Location(self):
        return self.calendar_event.Location()

    @property
    def Organizer(self):
        return self.calendar_event.Organizer()

    @property
    def Start(self):
        return pickle.dumps(self.calendar_event.Start())

    @property
    def Subject(self):
        return self.calendar_event.Subject()
