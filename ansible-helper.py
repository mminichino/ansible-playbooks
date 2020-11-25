#!/usr/bin/env python
#
# Ansible Playbook helper utility
#

import getopt
import sys
import os
import stat
import subprocess
import json
import re
import fnmatch
import readline

class ErrorExit(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

def myinput(prompt, prefill):
    def hook():
        readline.insert_text(prefill)
        readline.redisplay()
    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result

class argset:

    def __init__(self):
        self.argname = []
        self.optdash = []
        self.longlist = []
        self.shortlist = ''
        self.extravars = []
        self.extraname = []
        self.checkarg = False
        self.printarg = False
        self.debugarg = False
        self.savearg = False
        self.readarg = False
        self.listarg = False
        self.saveFileKey = None
        self.addArg("c", "check", True)
        self.addArg("p", "print", True)
        self.addArg("d", "debug", True)
        self.addArg("l", "list", True)
        self.addArg("h", "help", True)
        self.addArg("s", "save", False)
        self.addArg("r", "read", False)

        try:
            self.playbook = sys.argv[1]
            sys.argv.pop(1)
        except IndexError as e:
            print("Playbook should be first argument. Can not open playbook: %s" % str(e))
            sys.exit(1)

    def print_help(self, *args):
        if args:
            for errText in args:
                print("[!] Error: " + errText)
            sys.exit(1)
        else:
            print("Usage: " + sys.argv[0] + " playbook.yaml [ -p | -l | -s save_key | -r save_key ] | [ -c | -d ] --extra_var1 value --extra_var2 value ...")
            sys.exit(1)

    def addArg(self, shortarg, longarg, isFlag):

        self.argname.append(longarg)
        optdash = '--' + longarg
        self.optdash.append(optdash)
        if isFlag:
            self.longlist.append(longarg)
        else:
            longarg = longarg + "="
            self.longlist.append(longarg)
        if shortarg:
            if isFlag:
                self.shortlist = self.shortlist + shortarg
            else:
                self.shortlist = self.shortlist + shortarg + ":"

    def parseArgs(self):

        try:
            options, remainder = getopt.getopt(sys.argv[1:], self.shortlist, self.longlist)
        except getopt.GetoptError as e:
            print("Can not parse arguments: %s" % str(e))
            self.print_help()

        for opt, arg in options:
            if opt in ('-h', '--help'):
                self.print_help()
            elif opt in ('-c', '--check'):
                self.checkarg = True
            elif opt in ('-d', '--debug'):
                self.debugarg = True
            elif opt in ('-p', '--print'):
                if len(options) != 1:
                    print("Print option can not be combined with other options.")
                    sys.exit(1)
                self.printarg = True
                self.printArgs()
            elif opt in ('-l', '--list'):
                if len(options) != 1:
                    print("List option can not be combined with other options.")
                    sys.exit(1)
                self.listarg = True
            elif opt in ('-s', '--save'):
                if len(options) != 1:
                    print("Save option can not be combined with other options.")
                    sys.exit(1)
                if re.findall('[^a-zA-Z0-9-_]', arg):
                    print("Save key should not contain special characters.")
                    sys.exit(1)
                self.savearg = True
                self.saveFileKey = arg
            elif opt in ('-r', '--read'):
                if len(options) != 1 and self.checkarg == False and self.debugarg == False:
                    print("Read option can not be combined with other options.")
                    sys.exit(1)
                self.readarg = True
                self.saveFileKey = arg
            elif opt in self.optdash:
                optname = opt.strip('--')
                extravaritem = '"' + optname + '":"' + arg + '"'
                self.extravars.append(extravaritem)

    def parsePlaybook(self):

        try:
            with open(self.playbook, 'r') as yamlfile:
                for line in yamlfile:
                    if line.startswith('#') and 'var:' in line:
                        varline = line.split(':')
                        if (len(varline) > 1):
                            variable = varline[1].rstrip("\n")
                            self.addArg(None, variable, False)
                            self.extraname.append(variable)
        except OSError as e:
            print("Can not open playbook: %s" % str(e))
            sys.exit(1)

    def printArgs(self):
            for x in range(len(self.optdash)):
                print (self.optdash[x])
            sys.exit(0)

class playrun:

    def __init__(self, argclass):

        self.runargs = argclass
        self.saveFileVersion = 3
        self.playDirname = os.path.dirname(self.runargs.playbook)
        if not self.playDirname:
            self.playDirname = '.'
        self.playBasename = os.path.basename(self.runargs.playbook)
        self.playName = os.path.splitext(self.playBasename)[0]
        self.playSaveFile = self.playDirname + "/" + self.playName + ".save"
        self.playSaveContents = {}

    def listSavedPlays(self):
        self.storeSavedPlay()
        if self.playSaveContents:
            print("Saved plays for %s" % self.playBasename)
            for key in self.playSaveContents:
                print("- %s" % key)
                for subkey in self.playSaveContents[key]:
                    print("  - %s => %s (prompt=%s)" % (subkey, self.playSaveContents[key][subkey]['value'], self.playSaveContents[key][subkey]['prompt']))
        else:
            print("No save files have been created for playbook.")
            print("%s not found" % self.playSaveFile)

    def readSavedPlay(self):
        self.storeSavedPlay()
        if not self.runargs.saveFileKey in self.playSaveContents:
            print("Scenario %s not saved for playbook %s" % (self.runargs.saveFileKey, self.playBasename))
            sys.exit(1)
        key = self.runargs.saveFileKey
        for subkey in self.playSaveContents[key]:
            saveParamvalue = self.playSaveContents[key][subkey]['value']
            promptParam = self.playSaveContents[key][subkey]['prompt']
            if promptParam == 'true':
                answer = myinput(subkey + ": ", saveParamvalue)
                answer = answer.rstrip("\n")
                saveParamvalue = answer
            extravaritem = '"' + subkey + '":"' + saveParamvalue + '"'
            self.runargs.extravars.append(extravaritem)

    def storeSavedPlay(self):
        if os.path.exists(self.playSaveFile):
            try:
                with open(self.playSaveFile, 'r') as saveFile:
                    try:
                        saveData = json.load(saveFile)
                    except ValueError as e:
                        print("Save file does not contain valid JSON data: %s" % str(e))
                        sys.exit(1)
                    saveFileIter = iter(saveData)
                    for key in saveData:
                        if key == 'saveFileVersion':
                            if saveData[key] != self.saveFileVersion:
                                print("Save file version error, file version %s required version %s" % (saveData[key], self.saveFileVersion))
                                sys.exit(1)
                            continue
                        if key == 'playbookBaseName':
                            if saveData[key] != self.playBasename:
                                print("Playbook name mismatch, got %s expecting %s" % (saveData[key], self.playBasename))
                                sys.exit(1)
                            continue
                        self.playSaveContents[key] = saveData[key]
            except OSError as e:
                print("Could not read save file: %s" % str(e))
                sys.exit(1)

    def savePlay(self):

        if not self.runargs.saveFileKey:
            raise ErrorExit("savePlay: Error: saveFileKey not defined")
        self.storeSavedPlay()
        try:
            saveData = {"saveFileVersion" : self.saveFileVersion, "playbookBaseName" : self.playBasename}
            if self.playSaveContents:
                for key in self.playSaveContents:
                    saveData[key] = self.playSaveContents[key]
            if not self.runargs.saveFileKey in saveData:
                saveData[self.runargs.saveFileKey] = {}
            with open(self.playSaveFile, 'w') as saveFile:
                for x in range(len(self.runargs.extraname)):
                    inputOptText = input(self.runargs.extraname[x] + ": ")
                    inputOptText = inputOptText.rstrip("\n")
                    if inputOptText != '':
                        optText = self.runargs.extraname[x]
                        paramBlock = {optText : {}}
                        inputPromptText = input("Prompt? (y/n) [n]: ")
                        inputPromptText = inputPromptText.rstrip("\n")
                        keyValueOpt = { 'value' : inputOptText }
                        if inputPromptText == 'y':
                            promptValue = 'true'
                        else:
                            promptValue = 'false'
                        keyValuePrompt = { 'prompt' : promptValue }
                        paramBlock[optText].update(keyValueOpt)
                        paramBlock[optText].update(keyValuePrompt)
                        saveData[self.runargs.saveFileKey].update(paramBlock)
                json.dump(saveData, saveFile, indent=4)
                saveFile.write("\n")
                saveFile.close()
        except OSError as e:
            print("Could not write save file: %s" % str(e))
            sys.exit(1)

    def runPlay(self):

        cmdlist = []
        runcmd = ''
        extravarjson = ''

        if self.runargs.extravars:
            extravarjson = '\'{'
            for x in range(len(self.runargs.extravars)-1):
                extravarjson = extravarjson + self.runargs.extravars[x] + ','
            extravarjson = extravarjson + self.runargs.extravars[-1] + '}\''
            extravarexec = '--extra-vars ' + extravarjson
        else:
            extravarexec = ''

        cmdlist.append("ansible-playbook")
        cmdlist.append(self.runargs.playbook)
        cmdlist.append(extravarexec)
        if self.runargs.checkarg:
            cmdlist.append('--check')
        if self.runargs.debugarg:
            cmdlist.append('-vvv')

        for x in range(len(cmdlist)):
            if (x == 0):
                runcmd = cmdlist[x]
            else:
                runcmd = runcmd + ' ' + cmdlist[x]

        print (runcmd)
        os.system(runcmd)

def main():

    os.environ['ANSIBLE_HOST_KEY_CHECKING'] = 'False'

    runArgs = argset()
    runArgs.parsePlaybook()
    runArgs.parseArgs()

    playRun = playrun(runArgs)
    if runArgs.listarg:
        playRun.listSavedPlays()
    elif runArgs.savearg:
        playRun.savePlay()
    elif runArgs.readarg:
        playRun.readSavedPlay()
        playRun.runPlay()
    else:
        playRun.runPlay()

if __name__ == '__main__':

    try:
        main()
    except SystemExit as e:
        if e.code == 0:
            os._exit(0)
        else:
            os._exit(e.code)
