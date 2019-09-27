import re

def config(options):
    pass

class A:
    def h(self):
        if len(self.in_buffer) > 0:
            messages = re.split(b'[\r\n]+', self.in_buffer)
            if messages[-1] != b'':
                self.in_buffer = messages[-1]
            else:
                self.in_buffer = b''
            for message in messages[:-1]:
                print(message)
