from extronlib.engine.IpcpLink import ExtronNode
_debug = False
import traceback
import base64

class RFile(ExtronNode):
    """ Access to restricted files. These files can only be created and accessed within the program. Files can be uploaded to provide initial values via the Global Scripter® project.

    ---

    Arguments:
        - Filename (string) - Name of file to open
        - mode (string) - the mode in which the files is opened.
        - encoding (string) - the name of the encoding used to decode/encode the file.
        - newline (string) - controls how universal newlines mode works

    Note:
        - mode, encoding, and newline have the same meanings as those passed to the built-in function open(). See the documentation at python.org.
        - ChangeDir(), DeleteDir(), DeleteFile(), Exists(), GetCurrentDir(), ListDir(), MakeDir(), and RenameFile() are all classmethods.

    Note: For restricted file access, substitute File with RFile in the examples above and below.

    ---

    Parameters:
        - Filename - Returns (string) - name of file
    """


    def ChangeDir(path: str,ipcp_index=0):
        from extronlib.engine import IpcpLink
        IpcpLink.ipcp_links[ipcp_index].RFile.ChangeDir(path)
    def DeleteDir(path: str,ipcp_index=0):
        from extronlib.engine import IpcpLink
        IpcpLink.ipcp_links[ipcp_index].RFile.DeleteDir(path)
    def DeleteFile(filename: str,ipcp_index=0):
        from extronlib.engine import IpcpLink
        IpcpLink.ipcp_links[ipcp_index].RFile.DeleteFile(filename)
    def Exists(path: str,ipcp_index=0):
        from extronlib.engine import IpcpLink
        return(IpcpLink.ipcp_links[ipcp_index].RFile.Exists(path))
    def GetCurrentDir(ipcp_index=0):
        from extronlib.engine import IpcpLink
        return(IpcpLink.ipcp_links[ipcp_index].RFile.GetCurrentDir())
    def ListDir(path: str=None,ipcp_index=0):
        from extronlib.engine import IpcpLink
        return(IpcpLink.ipcp_links[ipcp_index].RFile.ListDir(path))
    def MakeDir(path: str,ipcp_index=0):
        from extronlib.engine import IpcpLink
        IpcpLink.ipcp_links[ipcp_index].RFile.MakeDir(path)
    def RenameFile(oldname: str, newname: str,ipcp_index=0):
        from extronlib.engine import IpcpLink
        IpcpLink.ipcp_links[ipcp_index].RFile.RenameFile(oldname,newname)




    def __enter__(self):return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
    def __iter__(self):
        #query file contents
        seq = self._Query('readlines',[])
        l = []
        for data in seq:
            data = base64.b64decode(data)
            if 't' == self.mode:
                data = data.decode()
            yield(data)

    _type='RFile'
    def __init__(self, Filename: str, mode: str='r', encoding: str=None, newline: str=None,ipcp_index=0) -> None:
        """ RFile class constructor.

        Arguments:
            - Filename (string) - Name of file to open
            - mode (string) - the mode in which the files is opened.
            - encoding (string) - the name of the encoding used to decode/encode the file.
            - newline (string) - controls how universal newlines mode works
        """
        self.Filename = Filename
        self.mode = mode
        self.encoding = encoding
        self.newline = newline


        self.ChangeDir = self.__ChangeDir
        self.DeleteDir = self.__DeleteDir
        self.DeleteFile = self.__DeleteFile
        self.Exists = self.__Exists
        self.GetCurrentDir = self.__GetCurrentDir
        self.ListDir = self.__ListDir
        self.MakeDir = self.__MakeDir
        self.RenameFile = self.__RenameFile


        if self.Filename:
            self._args = [Filename,mode,encoding,newline]
        else:
            self._args = []
        self._ipcp_index = ipcp_index
        self._alias = f'RF:{Filename}:{mode}:{encoding}:{newline}'
        self._callback_properties = {}
        self._properties_to_reformat = []
        self._query_properties_init = {}
        self._query_properties_always = {}
        super().__init__(self)
        self._initialize_values()
    def _initialize_values(self):
        self._query_properties_init_list = list(self._query_properties_init.keys())
    def __format_parsed_update_value(self,property,value):
        if property in self._properties_to_reformat:
            if property == 'ReceiveData':
                if type(value) == list:
                    value = value[0]
                value = base64.b64decode(value)
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


    def __ChangeDir(self, path: str) -> None:
        """ Change the current working directory to path

        Arguments:
            - path (string) - path to directory
        """
        if not self.Filename:self._Command('ChangeDir',[path])
        else:self.ipcp_link.RFile.ChangeDir(path)

    def __DeleteDir(self, path: str) -> None:
        """ Remove a directory

        Arguments:
            - path (string) - path to directory
        """
        if not self.Filename:self._Command('DeleteDir',[path])
        else:self.ipcp_link.RFile.DeleteDir(path)

    def __DeleteFile(self, filename: str) -> None:
        """ Delete a file

        Arguments:
            - filename (string) - the name of the file to be deleted (path to file)
        """
        #self._Command('DeleteFile',[filename])
        if not self.Filename:self._Command('DeleteFile',[filename])
        else:self.ipcp_link.RFile.DeleteFile(filename)

    def __Exists(self, path: str) -> bool:
        """ Return True if path exists

        Arguments:
            - path (string) - path to directory

        Returns
            - true if exists else false (bool)
        """
        if not self.Filename:return(self._Query('Exists',[path]))
        else:return(self.ipcp_link.RFile.Exists(path))

    def __GetCurrentDir(self) -> str:
        """ Get the current path.

        Returns
            - the current working directory (string)
        """
        if not self.Filename:return(self._Query('GetCurrentDir',[]))
        else:return(self.ipcp_link.RFile.GetCurrentDir())

    def __ListDir(self, path: str=None) -> str:
        """ List directory contents

        Arguments:
            - path (string) - if provided, path to directory to list, else list current directory

        Returns
            - directory listing (string)
        """
        if not self.Filename:return(self._Query('ListDir',[path]))
        else:return(self.ipcp_link.RFile.ListDir(path))

    def __MakeDir(self, path: str) -> None:
        """ Make a new directory

        Arguments:
            - path (string) - path to directory
        """
        if not self.Filename:self._Command('MakeDir',[path])
        else:self.ipcp_link.RFile.MakeDir(path)

    def __RenameFile(self, oldname: str, newname: str) -> None:
        """ Rename a file from oldname to newname

        Arguments:
            - oldname (string) - the original filename
            - newname (string) - the filename to rename to
        """
        if not self.Filename:self._Command('RenameFile',[oldname,newname])
        else:self.ipcp_link.RFile.RenameFile(oldname,newname)

    def close(self) -> None:
        """ Close an already opened file
        """
        self._Command('close',[])

    def read(self, size: int=-1) -> bytes:
        """ Read data from opened file

        Arguments:
            - size (int) - max number of char/bytes to read

        Returns
            - data (bytes)
        """
        b = self._Query('read',[size])
        val = base64.b64decode(b)
        return val

    def readline(self) -> bytes:
        """ Read from opened file until newline or EOF occurs

        Returns
            - data (bytes)
        """
        b = self._Query('readline',[])
        val = base64.b64decode(b)
        return val


    def seek(self, offset: int, whence: int=0) -> None:
        """ Change the stream position

        Arguments:
            - offset (int) - offset from the start of the file
            - (optional) whence (int) -
                - 0 = absolute file positioning
                - 1 = seek relative to the current position
                - 2 = seek relative to the file’s end.

        Note: Files opened in text mode (i.e. not using 'b'), only seeks relative to the beginning of the file are allowed – the exception being a seek to the very file end with seek(0,2).
        """
        self._Command('seek',[offset,whence])

    def tell(self) -> int:
        """ Returns the current cursor position

        Returns
            - the current cursor position (int)
        """
        self._Query('tell',[])

    def write(self, data) -> None:
        """ Write string or bytes to file

        Arguments:
            - data (string, bytes) - data to be written to file
        """
        if type(data) == str:
            data = data.encode()
        val = base64.b64encode(data).decode('utf-8')
        self._Command('write',[val])

    def writelines(self, seq: list) -> None:
        """ Write iterable object such as a list of strings

        Arguments:
            - seq (e.g. list of strings) - iterable sequence

        Raises:
            - FileNotOpenError
        """
        l = []
        for data in seq:
            if type(data) == str:
                data = data.encode()
            l.append(base64.b64encode(data).decode('utf-8'))
        self._Command('writelines',[l])
