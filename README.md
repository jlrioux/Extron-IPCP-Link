# Server-Side Extronlib Package
## Abstract
The goal of this package is to allow for as much processing for Extron control systems to occur on a networked server as possible, freeing up the IPCP Pro control processor to handle port communications and Extron specific hardware communications.  It is also designed to function for both Qxi and non-Qxi controllers.
The Server can be either Windows or Linux.


## Implementation
To implement the package, drop the extronlib folder into your working directory and insert the following lines into the top of your entry file.  You should not have to make any other changes from normal Extron ControlScript programming.
```
from extronlib.engine import IpcpLink
link = IpcpLink('172.16.1.10','AVLAN')
```
PARAMETERS
ip_address- The ip address of the control processor.
port- Optional. Either 'LAN' or 'AVLAN' depending on which port the server will communicate with that controller. The default value is 'LAN'
password- Optional. The Passowrd to use for this communication purpose. The default password is 'p9oai23jr09p8fmvw98foweivmawthapw4t'


## Requires
Python Versions: 3.10 through 3.13 have been tested to work
non-standard packages required: paramiko, schedule.  Please use pip to install these.

To execute, run your mainfile with the cwd as the directory of your mainfile.


## Operational Notes
### File Access
Files read and written by the File implementation are stored in /extronlib/engine/RAM/
RFile reaches over the network to the IPCP controller to access its RFILE storage.

### SSL Certificates
It isn't posslbe to serialize and transfer SSL certificates from the IPCP for use on the Server.
There is a folder designated for this and the Certificates should be stored in /extronlib/engine/SSL Certificates/
The functions of using specific certificates other than the default for your OS are not currently implemented in this implementation of the extronlib package.
You may modify /extronlib/system/__init__.py and implement the SSL functions as you wish.

### Optional IPCP Processing For Certain Interfaces
EthernetClientInterface, EthernetServerInterfaceEx, EthernetServerInterface all have the optional parameter, "thru_ipcp", in their constructors to be defined on the IPCP instead of the Server.  This can be especially handy if you need to SSL wrap your EthernetServerInterface and use the SSL Certificate on the IPCP Controller.
The default behavior is to have this processing on the Server.


## Behavioral Notes
### In the event only the IPCP processor is rebooted
Commands stop being issued to the IPCP and the Server begins a "reconnect loop",
Once connected, the Server runs through all devices and objects to re-instantiate them on the IPCP server as needed.
Control system Operations then resume as normal.  During this process, any Timers and Waits will continue to execute, although functions through the IPCP will not actually be sent.  SendAndWaits will return '' and queries will return null values.

### In the event only the Server is restarted
When the program boots back up, it runs through all of the code as normal, but the delay of object instantiation on the IPCP side is skipped as they already exist.
The IPCP simply reports that the initialization of that object is complete.


## Known Issues
### Further testing is needed
-I have yet to test through some object types to which do not have access.
SummitConnect
DanteInterface
SWACRecepticalInterface
SWPowerInterface

-While the architecture was designed to allow for multiple Servers to access the IPCP and its objects at once, more testing is required to ensure full reliability.
-Server-side SSL wrapping of EthernetServerInterfaceEx needs to be implemented, use thru_ipcp option if needed for now.


# IPCP-Side Extronlib Package
## Implementation
Set up the JSON configuration file to load with CSDU like normal with the TP file in the layout folder and IR files in the IR file as normal.
The main.py file in SRC can be modified to disable either the LAN or AVLAN connection as needed and an optional parameter of the WrapperBasics class can supply a custom password.
The default password is 'p9oai23jr09p8fmvw98foweivmawthapw4t'


## Operational Notes
### Touch Panel Considerations
The "Where Used" list within GUI Designer should be exported in CSV format with the same name as your panel's alias.  This CSV file should be loaded to the IPCP controller in the RFILE directory.
Failure to do this will result in much slower boot times when large touch panel GUIs are used.
This also prevents the annoying non-error of id's not being valid from filling up the Program Log.
When the user interface has elements added or removed from it, the CSV should be remade.


## Known Issues
### Further testing is needed
-I have yet to test through some object types to which do not have access.
SummitConnect
DanteInterface
SWACRecepticalInterface
SWPowerInterface

-While the architecture was designed to allow for multiple Servers to access the IPCP and its objects at once, more testing is required to ensure full reliability.

## Credits
Author - Jean-Luc Rioux