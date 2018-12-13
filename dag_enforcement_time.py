#!/usr/bin/env python

################################################
###   DAG Enforcement Time for Kiev 9.0.0  #####
###   Author: Vinaykumar Muralidharan      #####
################################################

import re, sys, os, time, pexpect
import threading
import Queue
from pprint import pprint as p
sys.path.append('../libModules')
sys.path.append('/home/ubuntu/pythonScripts/libModules/')
from panFwCli import *
from panLogs import *
from panUtils import *
import subprocess
from datetime import datetime



###Getting Fire wall Access
drawLine()
fwIp = <Firewall IP>
fwHandler=Panfw_Cli('admin', fwIp, 'admin')
fwHandler._ssh_connect_admin()
build=fwHandler._cli_find_installed_build()
print "Logging on to the Firewall" + fwIp
print "Firewall Version:"+build
drawLine()

#numMappings = [1,5,10,20,50,100,150,200,250,500,1000,5000,10000,15000,20000,25000,30000,35000,40000,45000,50000,55000,60000,65000]
numMappings = [1000,5000,10000,15000,20000,25000,30000,35000,40000,45000,50000,55000,60000,65000]
pingIPList = ['172.17.1.2', '172.17.1.50', '172.17.1.100', '172.17.2.2', '172.17.2.50', '172.17.2.100', '172.17.3.2', '172.17.3.50', '172.17.3.100','172.17.3.150']

#numMappings = [25000]

def pingIp(ip):
    _ = 'ping -c 100 '+ip+' | while read pong; do echo "$(date +"%Y-%m-%d %T"): $pong"; done > ping_test.txt &' 
    #print _
    p1 = subprocess.Popen(_, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
def xmlTagReg(action, numTag, fwIp, vsys, seed, subnet):
    _ = 'python dag_tag.py -A '+action+' -i '+numTag+' -H '+fwIp+' -p admin -v '+vsys+' -s '+seed+' -I '+ subnet
    print _
    p2 = subprocess.Popen(_, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(10)
    return(p2.stdout.read())
    
fp = open('dag_timing_file.txt','w')
###For Loop
for i in range(len(numMappings)):

    ###Clearing all the IP-TAG mappings on the Fire wall
    #drawLine("Clearing all the IP-TAG mappings on the Fire wall")
    arr=['set system setting target-vsys vsys1', 'debug object registered-ip clear all']
    log=fwHandler._send_cli_command(arr)
    #print log
    time.sleep(5)


    ###Starting PING traffic to IP-TAG Matched IP in Policy
    os.remove('ping_test.txt')
    #drawLine("Starting PING traffic to IP-TAG Matched IP in Policy")
    pingIp('172.16.1.2')
    

    ###Using PanXapi Send XML-API Mapping
    #drawLine("Using PanXapi Send XML-API Mapping")
    if numMappings[i] > 250:
        tmp1 = xmlTagReg('register',str(numMappings[i]) ,fwIp, 'vsys1','0', '172.16.0.0/16' )
    else:
        tmp1 = xmlTagReg('register',str(numMappings[i]) ,fwIp, 'vsys1','0', '172.16.1.0/24' )

    ###Get the Time stamp of Success message from the Fire wall for XML-API Mapping
    xmlStartTime =  re.findall('(\d+-\d+-\d+ \d+:\d+:\d+) Start Execution of XML-API',tmp1)[0]
    xmlTime = re.findall('(\d+-\d+-\d+ \d+:\d+:\d+) SUCCESS dynamic-update: success',tmp1)[0]
    #print 'xmlTime: ' + xmlTime

    ###Get the Time stamp of first successful PING response
    time.sleep(10)
    tmp = open('ping_test.txt', 'r')
    _ = tmp.read()
    pingTime=re.findall('(\d+-\d+-\d+ \d+:\d+:\d+): 64 bytes from',_)[0]
    #print 'pingTime: ' + pingTime
    
    ###Calculate the Time taken for Policy enforcement
    fmt = '%Y-%m-%d %H:%M:%S'
    tstamp1 = datetime.strptime(xmlTime,fmt)
    tstamp2 = datetime.strptime(pingTime,fmt)
    tstamp3 = datetime.strptime(xmlStartTime,fmt)
    
    if tstamp1 > tstamp2:
        td = tstamp1 - tstamp2
    else:
        td = tstamp2 - tstamp1
        
    if tstamp1 > tstamp3:
        td2 = tstamp1 - tstamp3
    else:
        td2 = tstamp3 - tstamp1
    

    fp.write("Firewall IP: {} numMappings: {} XMLStartTime: {} XMLEndTime: {} Ping: {} XML-Consumption-Time: {} DP-Time-Difference: {}\n".format(fwIp,numMappings[i],xmlStartTime, xmlTime, pingTime, td2, td))
    drawLine("Firewall IP: {} numMappings: {} XMLStartTime: {} XMLEndTime: {} Ping: {} XML-Consumption-Time: {} DP-Time-Difference {}".format(fwIp,numMappings[i],xmlStartTime, xmlTime, pingTime,td2,  td))
    time.sleep(1)
    os.system("killall -9 ping");


### Plot the results 

fp.close()



