import subprocess
import os
import select
import queue
import threading

goodresponse = "Done."

class KernelHandler:
    def __init__(self, executable, inqueue, outqueue):
        self.executable = executable
        self.proc = subprocess.Popen(self.executable,
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     shell=True)
        self.inqueue = inqueue
        self.outqueue = outqueue
        
        self.kernel_thread = threading.Thread(target=self.run, name="KernelThread")
        self.kernel_thread.setDaemon(True)
        self.kernel_thread.start()
    
    def __del__(self):
        self.stop()
        self.kernel_thread.join()
        
    def _write(self, data):
        if not self.proc:
            raise Exception("Kernel not started")
        self.proc.stdin.write(data.encode())
        self.proc.stdin.flush()
    
    def _readline(self):
        if not self.proc:
            raise Exception("Kernel not started")
        data = ''
        while True:
            currentline = self.proc.stdout.readline().decode().strip()
            data = data + currentline
            # stop reading if there are an even number of "'s 
            if not data.count('\"') % 2:
                break
            # add back the newline that was swallowed
            data = data + '\n'
        return data
    
    def stop(self):
        self.go = False
        
    def checkresponse(self):
        response = self._readline()
        if not response == goodresponse:
            raise Exception("Kernel command failed. Response: " + response)
    
    def stats(self):
        self._write("stats\n")
        return (self._readline(), self._readline())
        
    def importorgs(self):
        while True:
            try:
                org = self.inqueue.get_nowait()
                self._write('insert ' + org + '\n')
                self.checkresponse()
            except queue.Empty:
                break
    
    def exportorgs(self, count=1):
        for n in range(0, count):
            self._write("pullrandom\n")
            org = self._readline()
            self.outqueue.put(org)
    
    def advance(self, count=1):
        for n in range(0, count):
            self._write('advance\n')
            self.checkresponse()
    
    def updatefitness(self):
        self._write('updatefitness\n')
        self.checkresponse()
    
    def sort(self):
        self._write('sort\n')
        self.checkresponse()
    
    def quit(self):
        self._write('quit\n')
    
    def run(self):
        self.go = True
        self.updatefitness()
        while self.go:
            self.importorgs()
            self.updatefitness()
            self.sort()
            self.advance()
            self.exportorgs()
        self.quit()