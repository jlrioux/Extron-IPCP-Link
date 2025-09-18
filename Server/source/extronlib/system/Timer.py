from threading import Thread,Lock
import time
import traceback

class Timer():
    """ The Timer class allows the user to execute programmed actions on a regular time differential schedule.

    Note:
        - The handler (Function) must accept exactly two parameters, which are the Timer that called it and the Count.
        - If the handler (Function) has not finished by the time the Interval has expired, Function will not be called and Count will not be incremented (i.e. that interval will be skipped).

    In addition to being used as a decorator, Timer can be named and modified.

    ---

    Arguments:
        - Interval (float) - How often to call the handler in seconds (minimum interval is 0.1s).
        - Function (function) - Handler function to execute each Interval.

    ---

    Parameters:
        - Count - Returns (int) - Number of events triggered by this timer.
        - Function - Returns (function) - Handler function to execute each Interval. Function must accept exactly two parameters, which are the Timer that called it and the Count.
        - Interval - Returns (float) - How often to call the handler in seconds.
        - State - Returns (string) - Current state of Timer ('Running', 'Paused', 'Stopped')

    ---

    Events:
        - StateChanged - (Event) Triggers when the timer state changes. The callback takes two arguments. The first is the Timer instance triggering the event and the second is a string ('Running', 'Paused', 'Stopped').
    """

    __lock = Lock()
    __current_id = 0

    def __get_next_id():
        Timer.__lock.acquire()
        Timer.__current_id += 1
        val = Timer.__current_id
        Timer.__lock.release()
        return val

    def __call__(self,func):
        """ Decorate a function to be the handler of an instance of the Timer class.

        The decorated function must have two parameters
        """
        if func is None:
            print('Timer Error: function is None')
            return
        def decorator(Interval):
            self.Function = func
            self.__run_wait__()
        return decorator(self.Interval)


    def __init__(self, Interval: float, Function: callable=None) -> None:
        """ Timer class constructor.

        Arguments:
            - Interval (float) - How often to call the handler in seconds (minimum interval is 0.1s).
            - Function (function) - Handler function to execute each Interval.
        """
        self.__id = -1
        self.Count = 0

        self.__process__ = None #type:Thread
        self.__process_active__ = -1

        self.Interval = Interval
        self.Function = Function
        if self.Function:
            self.__run_wait__()

    def Change(self, Interval: float) -> None:
        """ Set a new Interval value for future events in this instance.

        Arguments:
            - Interval (float) - How often to call the handler in seconds.

        """
        self.Interval = Interval
        self.Restart()

    def Pause(self) -> None:
        """ Pause the timer (i.e. stop calling the Function).

        Note: Does not reset the timer or the Count.
        """

        if self.__process_active__ > 0:
            self.__process_active__ = -1
            self.__process__.join()

    def Resume(self) -> None:
        """ Resume the timer after being paused or stopped.
        """
        if self.__process__:
            self.__run_wait__()

    def Restart(self) -> None:
        """Restarts the timer – resets the Count and executes the Function in Interval seconds."""
        self.__process_active__ = -1
        self.Count = 0
        self.__run_wait__()

    def Stop(self) -> None:
        """ Stop the timer.

        Note: Resets the timer and the Count.
        """
        self.__process_active__ = -1
        self.Count = 0

    def __run_wait__(self) -> None:
        self.__id = Timer.__get_next_id()
        self.__process_active__ = self.__id
        self.__process__ = Thread(target=self.__func__(self.__id,self.Interval,self.Function))
        self.__process__.start()


    def __func__(self,id,Time:'float',func) -> None:
        def __timer_instance_worker_function():
            while self.__process_active__ == id:
                time.sleep(Time)
                self.Count += 1
                if self.__process_active__ == id:
                    if func is not None:
                        try:
                            func(self,self.Count)
                        except Exception as e:
                            print('Error Executing Function in Timer: {}'.format(traceback.format_exc()))
        return __timer_instance_worker_function
