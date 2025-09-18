_debug = False






class Email():
    """ Class to send email using the configured mail settings. The confiured settings can be over ridden during instantiation.

    Note: default sender will be login username@unit-name or hostname@unit-name if there is no authentication. To override, call Sender()

    ---

    Arguments:
        - smtpServer (string) - ip address or hostname of SMTP server
        - port (int) - port number
        - username (string) - login username for SMTP authentication
        - password (string) - login password for SMTP authentication
        - sslEnabled (bool) - Enable (True) or Disable (False) SSL for the connection
    """
    def __init__(self, smtpServer: str=None, port: int=None, username: str=None, password: str=None, sslEnabled: bool=None):
        """ Email class constructor.

        Arguments:
            - smtpServer (string) - ip address or hostname of SMTP server
            - port (int) - port number
            - username (string) - login username for SMTP authentication
            - password (string) - login password for SMTP authentication
            - sslEnabled (bool) - Enable (True) or Disable (False) SSL for the connection
        """
        self.smtpServer = smtpServer
        self.port = port
        self.username = username
        self.password = password
        self.sslEnabled = sslEnabled


        self._Sender = None
        self._Receiver = None
        self._Receiver_cc = None
        self._Subject = None
        self._Message = None



    def Receiver(self, receiver: list=None, cc: bool=False) -> None:
        """ Set receiver’s email address(es) by passing in a list of strings. For example, ['abc@extron.com‘,’xyz@extron.com‘] It will appear in the <To::: receiver> field of the email. If cc is set to True, it will appear in the <CC::: receiver> field of the email.

        Arguments:
            - receiver (list of strings) - receiver’s email address(es)
            - (optional) cc (bool) - Set True to put the receiver address(es) in the cc list

        Note: Receiver() must be called each time the list changes.

        """
        if cc:
            self._Receiver_cc = receiver
        else:
            self._Receiver = receiver



    def SendMessage(self, msg:str,ipcp_index=0) -> None:
        """ Create main body of the email and send out. Message string will be sent out as plain text.


        Arguments:
            - msg (string) - message to send
        """

        self._Message = msg

        if self._Sender and self._Receiver and self._Subject and self._Message:
            data = {
                'smtpServer':self.smtpServer,
                'port':self.port,
                'username':self.username,
                'password':self.password,
                'sslEnabled':self.sslEnabled,
                'sender':self._Sender,
                'receiver':self._Receiver,
                'receivercc':self._Receiver_cc,
                'subject':self._Subject,
                'sendmessage':self._Message
            }
            from extronlib.engine.IpcpLink import IpcpLink
            IpcpLink.ipcp_links[ipcp_index].System._Command('SendEmail',[data])








    def Sender(self, sender: str) -> None:
        """ Set sender’s email address. It will appear in the <From: sender> field of the email.

        Arguments:
            - sender (string) - sender email address

        Note: Overrides default sender.
        """
        self._Sender = sender



    def Subject(self, subject: str) -> None:
        """ Set email’s subject. It will appear in the <Subject::: > field of the email.

        Arguments:
            - subject (string) - subject of the email
        """
        self._Subject = subject








