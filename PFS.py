
from cmd import Cmd
import os
import math
import datetime as dt
import pickle
from shutil import copy2

class PFS(Cmd):
    directories = []
    FCB = []
    fileData = []
    buffer = []
    fcbDictionary = {}
    PFS_filename = ''

    #Following is a constructor to intialise the class parameters.  Also, a few
    #directories and files needed
    #for backgroud support would be created.
    def __init__(self):        
        if not os.path.exists("PFS"):
            os.makedirs("PFS")
        os.chdir("PFS")
        if not os.path.exists("Files"):
            os.makedirs("Files")

        if not os.path.exists("pfs.txt"):
            with open("pfs.txt","w"): pass

        try:
            #load the last saved status of to list using the pickle
            #functionality
            pickle_in = open("pfs.txt","rb")
            self.directories = pickle.load(pickle_in)
        except EOFError:
            self.directories = []

        try:
            #load the last saved status of the File Control Block to Dictionary
            #using the pickle functionality
            if not os.path.exists("fcb.txt"):
                with open("fcb.txt","w") as fcb: pass
            pickle_fcb_in = open("fcb.txt","rb")
            self.fcbDictionary = pickle.load(pickle_fcb_in)
            pickle_fcb_in.close()
        except EOFError:
            self.fcbDictionary = {}

        try:
            #load the last saved status of the file data to list i.e.  buffer
            #using the pickle functionality
            if not os.path.exists("data_backup.txt"):
                with open("data_backup.txt","w") as data: pass

            pickle_dataBackup_in = open("data_backup.txt","rb")
            self.buffer = pickle.load(pickle_dataBackup_in)
            pickle_dataBackup_in.close()
            
        except EOFError:
            self.buffer = []
        return super().__init__()
    
    #Following function would initiate the PFS file system by creating pfs file
    def do_open(self,args):
        if not os.path.exists(self.PFS_filename):
            print("Creating PFS now....")
        with open(args,"w"): 
            print("File has been opened....")
        with open("fcb.txt","w"):
            print("File Control Block has initiated.....")
        self.PFS_filename = args
        pass

    #Following function would implement the transfer file from Unix/Windows
    #file system to the PFS
    def do_put(self,args):
        temp = []
        line = ''
        backup_line = ''
        str1 = ''
        startBlock = 0
        endBLock = 0
        remainingWords = ''
        charCnt = 0
        i = 0
        
        #with the help of start and end block, the data is initially
        #transferred to a buffer
        #the buffer would add the data with the consideration of 256 bytes per
        #block.
        #The blocks would then be transferred to the PFS from the buffer.
        startBlock = len(self.buffer)
        with open(args,"r") as readFile:        
            line = readFile.readline().replace("\n"," ")
            
            while line:
                line = remainingWords + line
                remainingWords = ''
                i = 0
                for ch in line:
                    if charCnt > 255:
                        remainingWords = line[charCnt:]
                        self.buffer.append(str1)
                        str1 = ''
                        charCnt = 0
                        backup_line = line
                        break
                    str1 = str1 + ch
                    charCnt = charCnt + 1                
                    i = i + 1
                line = readFile.readline().replace("\n"," ")
            if charCnt < 256 and len(str1) > 0:
                self.buffer.append(str1)
                str1 = ''
            if i <= len(backup_line):
                self.buffer.append(backup_line[i:])

        endBLock = len(self.buffer) - 1 

        # The new file details added to the directory dictionary.
        self.fcbDictionary[str(''.join(args.rsplit('/',1)[-1:]))] = [str(''.join(args.rsplit('/',1)[-1:])),str(dt.datetime.utcnow().date()),str(dt.datetime.utcnow().time()),str(math.ceil(((endBLock - startBlock) * 256))) + " bytes",str(startBlock),str(endBLock)]

        if not os.path.exists(self.PFS_filename):
            with open(self.PFS_filename,'w+') as pfs:
                for item in self.buffer:
                    pfs.write('%s\n' % item)

        else:
            with open(self.PFS_filename,'a+') as pfs:
                for item in self.buffer:
                    pfs.write('%s\n' % item)
        pass

    #Following function would implement the dir command i.e.  display the file
    #details
    def do_dir(self,args):    
        for item in self.fcbDictionary:
            print('\t'.join(self.fcbDictionary[item]))
        pass

    #Following function would transfer the file from PFS to the Unix/Windows
    #file system
    def do_get(self,arg):
        try:
            val = []
            val = self.fcbDictionary[str(''.join(arg.rsplit('/',1)[-1:]))]
            startBlock = int(val[len(val) - 2])
            endBlock = int(val[len(val) - 1])
            temp = []
            temp = self.buffer[startBlock:endBlock]
        
            with open("Files/" + arg,"w+") as file:
                for item in temp:
                    file.write("%s\n" % item)                    
            pass
        except:
            print("Invalid file name or Incorrect destination path!!!")
        pass

    #Following function would remove the specified file if exists in the PFS.
    #It would also maintain the contiguous memory allocation
    def do_rm(self,args):
        try:
            val = self.fcbDictionary[str(''.join(args.rsplit('/',1)[-1:]))]
            startBlock = int(val[len(val) - 2])
            endBlock = int(val[len(val) - 1])
            for i in range(startBlock,endBlock):                
                self.buffer[i] = ""

            if os.path.exists(self.PFS_filename):
                with open(self.PFS_filename,'w+') as pfs:
                    for item in self.buffer:
                        pfs.write('%s\n' % item)
            else:
                print("PFS does not exist")

            del self.fcbDictionary[args]

        except Exception as ex:
            print('Invalid File!!!')        
        pass

    #Following function would kill the entire specified PFS
    def do_kill(self,args):
        try:
            self.buffer.clear()
            self.fcbDictionary.clear()
            os.remove(args)
        except:
            print('Invalid File!!!')
        pass

    # Following function is similar to put command, but instead of transferring
    # a file, it would add the comments to the existing file in the PFS.
    def do_putr(self,args):
        try:
            arg = args.split(" ")
            fileName = arg[0]   
            comment = ""
            for item in range(1,len(arg)):
                comment = comment + arg[item] + " "
            val = self.fcbDictionary[fileName]
            startBlock = int(val[len(val) - 2])
            endBlock = int(val[len(val) - 1])
            self.buffer[endBlock] = self.buffer[endBlock] + str(comment)

            if os.path.exists(self.PFS_filename):
                with open(self.PFS_filename,'w+') as pfs:
                    for item in self.buffer:
                        pfs.write('%s\n' % item)
            else:
                print("File does not exists.....")

        except Exception as ex:
            print("Invalid File!!!",ex)
        pass

    #Following function would exit the PFS system and would also save the
    #status of the entire system using pickle functionality.
    def do_quit(self,args):
        print("Exitting System......")
        pickle_out = open("pfs.txt","wb")
        pickle.dump(self.directories,pickle_out)
        pickle_out.close()

        pickle_fcb_out = open("fcb.txt","wb")
        pickle.dump(self.fcbDictionary,pickle_fcb_out,protocol=pickle.HIGHEST_PROTOCOL)
        pickle_fcb_out.close()

        pickle_dataBackup_out = open("data_backup.txt","wb")
        pickle.dump(self.buffer,pickle_dataBackup_out,protocol=pickle.HIGHEST_PROTOCOL)
        pickle_dataBackup_out.close()
        raise SystemExit

# This is the main method i.e.  the start of execution
if __name__ == '__main__':
    prompt = PFS()
    prompt.prompt = 'PFS> '
    prompt.cmdloop('Starting PFS prompt....')