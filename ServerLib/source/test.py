from extronlib.system import File
with File('/DebugLogs/DebugLog-2025-08-26-15.csv','r') as file:
    for line in file:
        print(line)



'''
from extronlib.engine import IpcpLink
link = IpcpLink('172.16.1.10','AVLAN')


from extronlib.system import RFile
print(RFile.ListDir())
with RFile('protocol.txt','r') as file:
    #for line in file:
    #    print(line)
    print(file.ListDir())
    #file.MakeDir('/subfolder1')
    #print(file.ListDir())
    #print(file.Exists('subfolder1/testtest.txt'))
    #print(file.Exists('protocol.txt'))
    #print(file.ChangeDir('/'))
    #print(file.GetCurrentDir())
    #print(file.ListDir())

print(RFile.ListDir())

'''
