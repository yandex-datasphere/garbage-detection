import os
import json 
import subprocess

class ExifToolHelper_ascii_only(object):
    sentinel = "{ready}\r\n"
    def __init__(self, executable):
        self.executable = executable

    def __enter__(self):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self.process = subprocess.Popen(
            [self.executable, "-stay_open", "True",  "-@", "-"],
            universal_newlines=True,
            startupinfo=startupinfo,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return self

    def  __exit__(self, exc_type, exc_value, traceback):
        self.process.stdin.write("-stay_open\nFalse\n")
        self.process.stdin.flush()

    def execute(self, *args):
        args = args + ("-execute\n",)
        self.process.stdin.write(str.join("\n", args))
        self.process.stdin.flush()
        output = ""
        fd = self.process.stdout.fileno()
        while not output.endswith(self.sentinel):
            output += os.read(fd, 4096).decode('utf-8')
        return output[:-len(self.sentinel)]

    def get_metadata(self, *filenames):
        return json.loads(self.execute("-G", "-j", "-n", *filenames))



class ExifToolHelper(object):
    def __init__(self, executable):
        self.executable = executable
        
    def __enter__(self):
        return self
        
    def  __exit__(self, exc_type, exc_value, traceback):
        return self 

    def get_metadata(self, file_in):
        args = """{} -G -j -n "{}" """.format(self.executable, file_in)
        self.process = subprocess.Popen(args, stdin = subprocess.PIPE,stdout = subprocess.PIPE, shell=True)
        (stdout, stderr) = self.process.communicate()
        # result = stdout.decode('cp1251').replace("\'", "\"").splitlines()
        # dcc = {}
        # for line in result:
        #     splitted = line.split(':')
        #     dcc[splitted[0].strip()] = splitted[1].strip()
        return json.loads(stdout.decode('cp1251'))  