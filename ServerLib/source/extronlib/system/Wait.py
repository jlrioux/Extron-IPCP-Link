from threading import Thread,Lock
from datetime import datetime
import time



class Wait():
    """ The wait class allows the user to execute programmed actions after a desired delay without blocking other processor activity.

    In addition to being used as a one-shot (decorator), Wait can be named and reusable.

    ---

    Arguments:
        - Time (float) - Expiration time of the wait in seconds
        - Function (function) - Code to execute when Time expires

    ---

    Parameters:
        - Function - Returns (function) - Code to execute when Time expires.
        - Time - Returns (float) - Expiration time of the wait in seconds with 10ms precision.
    """

    __lock = Lock()
    __current_id = 0

    def __get_next_id():
        Wait.__lock.acquire()
        Wait.__current_id += 1
        val = Wait.__current_id
        Wait.__lock.release()
        return val

    def __call__(self,func):
        """ Decorate a function to be the handler of an instance of the Wait class.

        The decorated function must have two parameters
        """
        if func is None:
            print('Wait Error: function is None')
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

        self.__process__ = None #type:Thread
        self.__process_active__ = -1
        self.__total_slept_time = 0.0
        self.__total_time_to_sleep = 0.0


        self.Interval = Interval
        self.Function = Function
        if self.Function:
            self.__run_wait__()

    def Change(self, Time: float) -> None:
        """ Set a new Interval value for future events in this instance.

        Arguments:
            - Interval (float) - How often to call the handler in seconds.

        """
        self.Interval = Time
        self.Restart()


    def Add(self, Time: float) -> None:
        """ Set a new Interval value for future events in this instance.

        Arguments:
            - Interval (float) - How often to call the handler in seconds.

        """
        self.__total_time_to_sleep += Time

    def Restart(self) -> None:
        """Restarts the wait – resets the Count and executes the Function in Interval seconds."""
        self.__process_active__ = -1
        self.__run_wait__()

    def Cancel(self) -> None:
        """ Stop the wait.

        Note: Resets the wait and the Count.
        """
        self.__process_active__ = -1

    def __run_wait__(self) -> None:
        self.__id = Wait.__get_next_id()
        self.__process_active__ = self.__id
        self.__process_start_time = datetime.now()
        self.__total_slept_time = 0.0
        self.__total_time_to_sleep = self.Interval
        self.__process__ = Thread(target=self.__func__(self.__id,self.Interval,self.Function))
        self.__process__.start()


    def __func__(self,id,Interval:'float',func) -> None:
        def __wait_instance_worker_function():
            Time = Interval
            while self.__process_active__ == id:
                time.sleep(Time)
                current_sleep_time = datetime.now()
                self.__total_slept_time = (current_sleep_time - self.__process_start_time).total_seconds()
                if self.__total_slept_time >= self.__total_time_to_sleep:
                    if self.__process_active__ == self.__id:
                        self.__process_active__ = -1
                        if func is not None:
                            try:
                                func()
                            except Exception as e:
                                print('Error Executing Function in Wait: {}'.format(e))
                else:
                    Time = self.__total_time_to_sleep - self.__total_slept_time
        return __wait_instance_worker_function