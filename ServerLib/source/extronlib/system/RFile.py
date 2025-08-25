from typing import Union


class RFile():
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

    def __init__(self, Filename: str, mode: str='r', encoding: str=None, newline: str=None) -> None:
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

    def ChangeDir(self, path: str) -> None:
        """ Change the current working directory to path

        Arguments:
            - path (string) - path to directory
        """
        ...

    def DeleteDir(self, path: str) -> None:
        """ Remove a directory

        Arguments:
            - path (string) - path to directory
        """
        ...

    def DeleteFile(self, filename: str) -> None:
        """ Delete a file

        Arguments:
            - filename (string) - the name of the file to be deleted (path to file)
        """
        ...

    def Exists(self, path: str) -> bool:
        """ Return True if path exists

        Arguments:
            - path (string) - path to directory

        Returns
            - true if exists else false (bool)
        """
        ...

    def GetCurrentDir(self) -> str:
        """ Get the current path.

        Returns
            - the current working directory (string)
        """
        ...

    def ListDir(self, path: str=None) -> str:
        """ List directory contents

        Arguments:
            - path (string) - if provided, path to directory to list, else list current directory

        Returns
            - directory listing (string)
        """
        ...

    def MakeDir(self, path: str) -> None:
        """ Make a new directory

        Arguments:
            - path (string) - path to directory
        """
        ...

    def RenameFile(self, oldname: str, newname: str) -> None:
        """ Rename a file from oldname to newname

        Arguments:
            - oldname (string) - the original filename
            - newname (string) - the filename to rename to
        """
        ...

    def close(self) -> None:
        """ Close an already opened file
        """
        ...

    def read(self, size: int=-1) -> bytes:
        """ Read data from opened file

        Arguments:
            - size (int) - max number of char/bytes to read

        Returns
            - data (bytes)
        """
        ...

    def readline(self) -> bytes:
        """ Read from opened file until newline or EOF occurs

        Returns
            - data (bytes)
        """
        ...

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
        ...

    def tell(self) -> int:
        """ Returns the current cursor position

        Returns
            - the current cursor position (int)
        """
        ...

    def write(self, data) -> None:
        """ Write string or bytes to file

        Arguments:
            - data (string, bytes) - data to be written to file
        """
        ...

    def writelines(self, seq: list) -> None:
        """ Write iterable object such as a list of strings

        Arguments:
            - seq (e.g. list of strings) - iterable sequence

        Raises:
            - FileNotOpenError
        """
        ...
