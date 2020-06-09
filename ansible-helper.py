#!/usr/bin/env python
#

import getopt, sys, os, stat, subprocess

arglist = []
optlist = []
checkarg = False
printarg = False
debugarg = False
extravars = []
extravarjson = ''
cmdlist = []
playbook = sys.argv[1]
runcmd = ''

try:
    with open(playbook, 'r') as yamlfile:
        for line in yamlfile:
            if line.startswith('#'):
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

for x in range(len(optlist)):
    optitem = optlist[x] + "="
    optdash = '--' + optlist[x]
    arglist.append(optitem)
    optlist[x] = optdash

options, remainder = getopt.getopt(sys.argv[1:], 'cpd', arglist) 

for opt, arg in options:
    if opt in ('-c', '--check'):
        checkarg = True
    elif opt in ('-d', '--debug'):
        debugarg = True
    elif opt in ('-p', '--print'):
        printarg = True
        for x in range(len(optlist)):
            print optlist[x]
        sys.exit(0)
    elif opt in optlist:
        extravaritem = '"' + opt.strip('--') + '":"' + arg + '"'
        extravars.append(extravaritem)

extravarjson = '\'{'
for x in range(len(extravars)-1):
    extravarjson = extravarjson + extravars[x] + ','
extravarjson = extravarjson + extravars[-1] + '}\''

extravarexec = '--extra-vars ' + extravarjson

cmdlist.append("/usr/bin/ansible-playbook")
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

print runcmd
os.system(runcmd)
