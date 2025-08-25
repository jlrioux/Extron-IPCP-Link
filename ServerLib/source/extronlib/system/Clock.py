import threading,queue
try:
    import schedule
except:
    print("""
**********  PYTHON IMPORT ERROR **********
Could not import python library "schedule"
Please install this library using
pip install schedule
in the command prompt
*****************************************
""")
from datetime import datetime
import time

class Clock():
    """ The clock is used to create timed events. It will allow the user to schedule programmed actions to occur based on calendar time.

    Note:
        - When DST causes the clock to spring forward one hour, events scheduled within the skipped hour do not fire.
        - When DST causes the clock to fall back an hour, events scheduled within the repeated hour fire twice.

    ---

    Arguments:
        - Times (list of strings) - list of times (e.g. 'HH:MM:SS') of day to call Function
        - Days (list of strings) - list of weekdays to set alarm. If Days is omitted, the alarm is set for every weekday
        - Function (function) - function to execute when alarm time is up

    ---

    Parameters:
        - Days - Returns (list of strings) - list of days to execute
        > Note: list will be empty if it was not provided to the constructor (i.e. the Clock is set for every day).
        - Function - Returns (function) - Code to execute at given Times.
        > Note: Function must accept two parameters: the Clock object and datetime object.
        - State - Returns (string) - State of the clock device. ('Enabled', 'Disabled')
        - Times - Returns (list of strings) - list of times to execute.
        - WEEKDAYS - (dict) - days of the week dictionary {'Monday' ::: 0, 'Tuesday'::: 1, 'Wednesday'::: 2, 'Thursday'::: 3, 'Friday'::: 4, 'Saturday'::: 5, 'Sunday'::: 6}
    """

    def __clock_worker_function():
        while True:
            schedule.run_pending()
            time.sleep(1)
    __worker_base = None

    __index = 0
    def __init__(self, Times: list, Days: list=None, Function=None) -> None:
        """ Clock class constructor.

        Arguments:
            - Times (list of strings) - list of times (e.g. 'HH:MM:SS') of day to call Function
            - Days (list of strings) - list of weekdays to set alarm. If Days is omitted, the alarm is set for every weekday
            - Function (function) - function to execute when alarm time is up
        """
        Clock.__index += 1

        self.__id = Clock.__index
        if Clock.__worker_base is None:
            Clock.__worker_base = threading.Thread(target=Clock.__clock_worker_function)
            Clock.__worker_base.start()

        self.__alias = f'Clock{self.__id}'
        self.__jobqueue = queue.Queue()
        self.__worker_instance = None


        self.WEEKDAYS = {'Monday': 0,
                    'Tuesday': 1,
                    'Wednesday': 2,
                    'Thursday': 3,
                    'Friday': 4,
                    'Saturday': 5,
                    'Sunday': 6}
        self.Times = Times
        self.Days = Days
        if self.Days is None:
            self.Days = list(self.WEEKDAYS.keys())
        self.Function = Function
        self.State = 'Disabled'


    def Disable(self) -> None:
        """ Disable alarm """
        if self.State == 'Enabled':
            self.State = 'Disabled'
            self.__disable_jobs()


    def Enable(self) -> None:
        """ Enable alarm """
        if self.__can_be_enabled():
            self.State = 'Enabled'
            self.__enable_jobs()


    def SetDays(self, Days: list) -> None:
        """ Send string to licensed software

        Arguments:
            - Days (list of strings) - a list of Calendar days, as listed in WEEKDAYS
        """
        self.Days = Days
        if self.Days is None:
            self.Days = list(self.WEEKDAYS.keys())
        self.Disable()
        self.Enable()


    def SetTimes(self, Times: list) -> None:
        """ Set new alarm times

        Arguments:
            - Times (list of strings) - list of times (e.g. 'HH:MM:SS') of day to call Function
        """
        if len(Times) > 0:
            self.Times = Times
            self.Disable()
            self.Enable()







    def __can_be_enabled(self):
        if self.Function is not None and len(self.Times)>0 and self.Days is not None:
            return True
        return False


    def __enable_jobs(self):
        for Time in self.Times:
            if 'Monday' in self.Days:
                schedule.every().monday.at(Time).do(self.__jobqueue.put,self.__wrap_job_function(self.Function)).tag(self.__alias)
            if 'Tuesday' in self.Days:
                schedule.every().tuesday.at(Time).do(self.__jobqueue.put,self.__wrap_job_function(self.Function)).tag(self.__alias)
            if 'Wednesday' in self.Days:
                schedule.every().wednesday.at(Time).do(self.__jobqueue.put,self.__wrap_job_function(self.Function)).tag(self.__alias)
            if 'Thursday' in self.Days:
                schedule.every().thursday.at(Time).do(self.__jobqueue.put,self.__wrap_job_function(self.Function)).tag(self.__alias)
            if 'Friday' in self.Days:
                schedule.every().friday.at(Time).do(self.__jobqueue.put,self.__wrap_job_function(self.Function)).tag(self.__alias)
            if 'Saturday' in self.Days:
                schedule.every().saturday.at(Time).do(self.__jobqueue.put,self.__wrap_job_function(self.Function)).tag(self.__alias)
            if 'Sunday' in self.Days:
                schedule.every().sunday.at(Time).do(self.__jobqueue.put,self.__wrap_job_function(self.Function)).tag(self.__alias)
        self.__worker_instance = threading.Thread(target=self.__create_instance_worker_function())
        self.__worker_instance.start()


    def __disable_jobs(self):
        self.__jobqueue.empty()
        schedule.clear(self.__alias)

    def __create_instance_worker_function(self):
        def __clock_instance_worker_function():
            while self.State == 'Enabled':
                while self.__jobqueue.qsize() > 0:
                    job = self.__jobqueue.get()
                    try:
                        job()
                    except Exception as e:
                        print('Error Executing Function in Clock:{}'.format(e))
                time.sleep(1)
        return __clock_instance_worker_function


    def __wrap_job_function(self,func):
        def f():
            if func is not None:
                dt = datetime.now()
                try:
                    func(self,dt)
                except Exception as e:
                    print('Error Executing Function in Clock: {}'.format(e))
        return f


