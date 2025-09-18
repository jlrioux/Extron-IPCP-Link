from remotelib_qxi import WrapperBasics
rb1 = WrapperBasics('AVLAN')
rb2 = WrapperBasics('LAN')
rb1.remote_server.EnableRemoteServer()
rb2.remote_server.EnableRemoteServer()
