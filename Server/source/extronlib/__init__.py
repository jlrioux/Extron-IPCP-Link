from extronlib import device, interface, software, standard, system, ui
__all__ = ['Version', 'event']

def Version():
    """ Return the Extron Library version string in the form of <major>.<minor>.<revision>"""
    return 'extron lib simulator 1.0'


def event(Object, EventName):
    """ Decorate a function to be the handler of Object when EventName happens.

    The decorated function must have the exact signature as specified by the definition of EventName, which must appear in the Object class or one of its parent classes. Lists of objects and/or events can be passed in to apply the same handler to multiple events.
    """
    def decorator(func):
        setattr(Object, EventName, func)
    return decorator
