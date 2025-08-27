from extronlib.system import RFile

with RFile('protocol.txt','r') as file:
    print(file.ListDir())

#with RFile('protocol.txt','r') as file:
#    for line in file:
#        print(line)