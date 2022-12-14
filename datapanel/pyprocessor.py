import psutil


class Proc(object):
    # data structure for a process. The class properties are process attributes
    def __init__(self, proc_info):
        self.user = proc_info[0]
        self.pid = proc_info[1]
        self.cpu = proc_info[2]
        self.mem = proc_info[3]
        self.vsz = proc_info[4]
        self.rss = proc_info[5]
        self.tty = proc_info[6]
        self.stat = proc_info[7]
        self.start = proc_info[8]
        self.time = proc_info[9]
        self.cmd = proc_info[10]

    def to_str(self):
        totalmem = psutil.virtual_memory().total / 1024 / 1024
        percentage = float(self.mem) / 100
        res = "(" + str(round(totalmem * percentage, 1)) + "M)"
        hours = self.time.split(":")[0] + "h"
        # returns a string containing minimalistic info about hte process:
        # user, pid, command
        return 'pid: %s up time: %s mem consumption: %s%% %s' % (self.pid, hours, self.mem, res)
