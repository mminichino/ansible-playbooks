#!/usr/bin/env python
#

import getopt, sys, os, stat, subprocess, json, re, fnmatch, readline

def err_exit(*args):
    if args:
        for errText in args:
            print("[!] Error: " + errText)
        sys.exit(1)
    else:
        print("Usage: " + sys.argv[0] + " playbook.yaml --extra_vars [ -c | -p | -d | -l | -s save_key | -r save_key]")
        sys.exit(1)

def myinput(prompt, prefill):
    def hook():
        readline.insert_text(prefill)
        readline.redisplay()
    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result

arglist = []
optlist = []
checkarg = False
printarg = False
debugarg = False
savearg = False
readarg = False
listarg = False
saveFileVersion = 2
extravars = []
extravarjson = ''
cmdlist = []
try:
    playbook = sys.argv[1]
except IndexError:
    err_exit()
runcmd = ''
utilityConfigDir = os.environ['HOME'] + '/.ansible-helper'
saveFileKey = None

if not os.path.exists(utilityConfigDir):
    try:
        os.mkdir(utilityConfigDir)
    except OSError as err:
        err_exit(err)

try:
    with open(playbook, 'r') as yamlfile:
        for line in yamlfile:
            if line.startswith('#') and 'var:' in line:
                varline = line.split(':')
                if (len(varline) > 1):
                    variable = varline[1].rstrip("\n")
                    optlist.append(variable)
except EnvironmentError as err:
    print("Could not read playbook: %s" % err)
    sys.exit(1)

sys.argv.pop(1)
arglist.append("check")
arglist.append("print")
arglist.append("debug")
arglist.append("save")
arglist.append("read")

for x in range(len(optlist)):
    optitem = optlist[x] + "="
    optdash = '--' + optlist[x]
    arglist.append(optitem)
    optlist[x] = optdash

try:
    options, remainder = getopt.getopt(sys.argv[1:], 'cpdls:r:', arglist) 
except getopt.GetoptError as err:
    err_exit()

for opt, arg in options:
    if opt in ('-c', '--check'):
        checkarg = True
    elif opt in ('-d', '--debug'):
        debugarg = True
    elif opt in ('-p', '--print'):
        printarg = True
    elif opt in ('-l', '--list'):
        listarg = True
    elif opt in ('-s', '--save'):
        savearg = True
        saveFileKey = arg
    elif opt in ('-r', '--read'):
        readarg = True
        saveFileKey = arg
    elif opt in optlist:
        extravaritem = '"' + opt.strip('--') + '":"' + arg + '"'
        extravars.append(extravaritem)

if saveFileKey:
    if re.findall('[^a-zA-Z0-9-_]',saveFileKey):
        err_exit("Save key should not contain special characters.")

if readarg and savearg:
    err_exit("Read and save options are mutually exclusive.")

if printarg:
    if checkarg or debugarg or savearg or readarg or listarg:
        err_exit("Print option can not be combined with other options.")
    else:
        for x in range(len(optlist)):
            print (optlist[x])
        sys.exit(0)

if listarg:
    if checkarg or debugarg or savearg or readarg or printarg:
        err_exit("List option can not be combined with other options.")
    else:
        if os.path.exists(utilityConfigDir):
            utilityConfigDirContents = os.listdir(utilityConfigDir)
            count = 1
            print("Utility required save file version: %s" % str(saveFileVersion))
            for fname in utilityConfigDirContents:
                if fnmatch.fnmatch(fname, playbook + ".save.*"):
                    saveFileName = utilityConfigDir + '/' + fname
                    try:
                        with open(saveFileName, 'r') as saveFile:
                            saveData = json.load(saveFile)
                            if "saveFileVersion" in saveData:
                                savedVersion = next(iter(saveData))
                                fileSavedVersion = str(saveData['saveFileVersion'])
                            else:
                                fileSavedVersion = 'No Version'
                        saveKeyText = fname.replace(playbook + '.save.', '')
                        print(str(count) + ") " + saveKeyText + " version: " + fileSavedVersion + " (" + fname + ")")
                        count = count + 1
                    except EnvironmentError as err:
                        print("Could not read save file: %s" % err)
                        sys.exit(1)
            sys.exit(0)
        else:
            err_exit("No save files have been created.")

if readarg:
    playbookBaseName = os.path.basename(playbook)
    saveFileName = utilityConfigDir + '/' + playbookBaseName + '.save.' + saveFileKey
    try:
        with open(saveFileName, 'r') as saveFile:
            saveData = json.load(saveFile)
            saveFileIter = iter(saveData)
            if "saveFileVersion" in saveData:
                savedVersion = next(saveFileIter)
                if int(saveData['saveFileVersion']) < int(saveFileVersion):
                    print("Incompatible save file version %s, version %s is required." % (str(saveData['saveFileVersion']), str(saveFileVersion)))
                    sys.exit(1)
            else:
                print("Incompatible save file, save file version not defined.")
                sys.exit(1)
            savedPlaybook = next(saveFileIter)
            if savedPlaybook != playbookBaseName:
                err_exit("Playbook " + playbookBaseName + " does not match saved playbook " + savedPlaybook)
            for key in saveData[savedPlaybook]:
                saveParamvalue = saveData[savedPlaybook][key]['value']
                promptParam = saveData[savedPlaybook][key]['prompt']
                if promptParam == 'true':
                    answer = myinput(key + ": ", saveParamvalue)
                    answer = answer.rstrip("\n")
                    saveParamvalue = answer
                extravaritem = '"' + key + '":"' + saveParamvalue + '"'
                extravars.append(extravaritem)
    except EnvironmentError as err:
        print("Could not read save file: %s" % err)
        sys.exit(1)

if savearg:
    playbookBaseName = os.path.basename(playbook)
    saveFileName = utilityConfigDir + '/' + playbookBaseName + '.save.' + saveFileKey
    try:
        saveData = {"saveFileVersion" : saveFileVersion, playbookBaseName : {}}
        with open(saveFileName, 'w') as saveFile:
            for x in range(len(optlist)):
                inputOptText = input(optlist[x] + ": ")
                inputOptText = inputOptText.rstrip("\n")
                if inputOptText != '':
                    optText = optlist[x].strip('--')
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
                    saveData[playbookBaseName].update(paramBlock)
            json.dump(saveData, saveFile, indent=4)
            saveFile.write("\n")
            saveFile.close()
    except EnvironmentError as err:
        print("Could not write save file: %s" % err)
        sys.exit(1)
    sys.exit(0)

if extravars:
    extravarjson = '\'{'
    for x in range(len(extravars)-1):
        extravarjson = extravarjson + extravars[x] + ','
    extravarjson = extravarjson + extravars[-1] + '}\''
    extravarexec = '--extra-vars ' + extravarjson
else:
    extravarexec = ''

cmdlist.append("ansible-playbook")
cmdlist.append(playbook)
cmdlist.append(extravarexec)
if checkarg:
    cmdlist.append('--check')
if debugarg:
    cmdlist.append('-vvv')

for x in range(len(cmdlist)):
    if (x == 0):
        runcmd = cmdlist[x]
    else:
        runcmd = runcmd + ' ' + cmdlist[x]

print (runcmd)
os.system(runcmd)
