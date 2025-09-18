class MESet():
    """ The Mutually Exclusive set allows for the grouping of objects to allow easy selection of related items. For instance, a group of buttons could be grouped so that selecting one button deselects the others in the group.

    ---

    Compatible extronlib classes:
        - IOInterface (and any children):
            - extronlib.interface.RelayInterface
            - extronlib.interface.FlexIOInterface (Output only)
            - extronlib.interface.DigitalIOInterface (Output only)
            - extronlib.interface.SWPowerInterface
        - Button:

    ---

    Arguments:
        - Objects (list) - list of compatible objects

    Note:
        - Each object must have a method SetState.
        - SetState must take an integer argument.
        - Any object with a SetState function that takes an integer object is compatible with this class.
        - A programmer can create their own class and use it with MESet.

    ---

    Parameters:
        - Objects - Returns (list) - the list of objects to track
    """

    def __init__(self, Objects: list) -> None:
        """ MESet class constructor.

       Arguments:
            - Objects (list) - list of compatible objects
        """
        self.__selected_object
        self.Objects = Objects
        self.__object_states = {}

    def Append(self, obj: object) -> None:
        """ Add an object to the list

        Arguments:
            - obj (any) - any compatible object to add
        """
        if obj not in self.Objects:
            self.Objects.append(obj)
            self.__object_states[obj] = {'On':0,'Off':0}



    def GetCurrent(self) -> object:
        """ Gets the currently selected object in the group.

        Returns
            - the currently selected object in the group.
        """
        if self.__selected_object == -1:
            return None
        return self.Objects[self.__selected_object]

    def Remove(self, obj) -> None:
        """ Remove an object from the list

        Arguments:
            - obj (int or compatible object) - the object or the index of the object
        """
        if obj in self.Objects:
            index = self.Objects.index(obj)
            if index == self.__selected_object:
                self.__selected_object = -1
            self.Objects.remove(obj)
            del self.__object_states[obj]



    def SetCurrent(self, obj) -> None:
        """ Selects the current object in the group

        Arguments:
            - obj (int or compatible object) - the object or the index of the object

        Note: When None is passed in, all objects will be deselected.
        """
        if obj in self.Objects:
            index = self.Objects.index(obj)
            self.__selected_object = index
        else:
            self.__selected_object = -1
        count = 0
        for obj in self.Objects:
            if count != index:
                obj.SetState(self.__object_states[obj]['Off'])
            else:
                obj.SetState(self.__object_states[obj]['On'])
            count += 1

    def SetStates(self, obj, offState: int, onState: int) -> None:
        """ Selects the off and on states for the object (i.e. use states other than the default 0 and 1, respectively).

        Arguments:
            - obj (int or object) - the object or the index of the object
            - offState (int) - the ID of the deselected state
            - onState (int) - the ID of the selected state
        """
        if obj in self.__object_states:
            self.__object_states[obj] = {'On':0,'Off':0}
