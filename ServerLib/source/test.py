from pathlib import Path




p = Path.cwd()
print(p)

p = Path('{}{}'.format(Path.cwd(),'/test.txt'))
print(p)

try:
    handle = open(p,mode='w')
except Exception as e:
    print('File: Failed to open file :{}'.format(e))

handle.write('test')
handle.close()