import os
import subprocess
import argparse
import re
from datetime import datetime
from lxml import etree
import random
from string import ascii_uppercase
import random
import sys
from ipaddress import IPv6Network, IPv6Address





def genTag(numTag,numBits,seed):
    tags=[]
    for i in range(numTag):
        random.seed(int(seed))
        tags.append(''.join(random.choice(ascii_uppercase) for i in range(numBits)))
        #print sys.getsizeof(''.join(choice(ascii_uppercase) for i in range(numBits)))
    return tags


def execShell(tmp):
    p1=subprocess.Popen(tmp, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    error=p1.stderr.read()
    out=p1.stdout.read()
    print out
    test=re.findall('<response status=\"(\w+)\"',out)
    print datetime.now().strftime('%Y-%m-%d %H:%M:%S'), test[0].upper(), error
    return

def genRegXML(numIps,seed,IP,v6,mask):
    file=open('uidreg.xml','w')
    root = etree.Element('uid-message')
    type = etree.Element('type')
    type.text = 'update'
    payload=etree.Element('payload')
    register=etree.Element('register')
    count=0
    
    
    for i in range(0,255):
        for j in range(1,255):
            if(count<int(numIps)):
                if(v6=='no'):
                    if(mask==24):
                        entry=etree.Element('entry', ip=IP[0]+"."+str(j))
                    elif(mask==16):   
                         entry=etree.Element('entry', ip=IP[0]+"."+str(i)+"."+str(j))
                else:
                    print IP
                    random.seed(count)
                    network = IPv6Network(IP)
                    address = IPv6Address(network.network_address + random.getrandbits(network.max_prefixlen - network.prefixlen))
                    entry=etree.Element('entry', ip=str(address))
                tag = etree.Element('tag')
                tags=genTag(1,26,seed)
                for j in range(len(tags)):
                    #member=etree.Element('member', timeout="120")
                    #member=etree.Element('member', timeout="86400")
                    #member=etree.Element('member', persistent='0')
                    #member=etree.Element('member', persistent='1')
                    member=etree.Element('member')
                    member.text=tags[j]
                    tag.append(member)
                entry.append(tag)
                register.append(entry)
            count+=1
    payload.append(register)
    root.append(type)
    root.append(payload)
    s = etree.tostring(root, pretty_print=True)
    print s
    file.write(s)
    file.close()
    
    
    
def genUnregXML(numIps,seed,IP,v6,mask):
    file=open('uidunreg.xml','w')
    root = etree.Element('uid-message')
    type = etree.Element('type')
    type.text = 'update'
    payload=etree.Element('payload')
    register=etree.Element('unregister')
    count=0
    for i in range(0,255):
        for j in range(1,255):
            if(count<=int(numIps)):
                if(v6=='no'):
                    if(mask==24):
                        entry=etree.Element('entry', ip=IP[0]+"."+str(j))
                    elif(mask==16):   
                         entry=etree.Element('entry', ip=IP[0]+"."+str(i)+"."+str(j))
                else:
                    random.seed(int(seed))
                    network = IPv6Network(IP)
                    address = IPv6Address(network.network_address + random.getrandbits(network.max_prefixlen - network.prefixlen))
                    entry=etree.Element('entry', ip=str(address))
                tag = etree.Element('tag')
                tags=genTag(1,26,seed)
                for j in range(len(tags)):
                    member=etree.Element('member', timeout="86400")
                    member.text=tags[j]
                    tag.append(member)
                entry.append(tag)
                register.append(entry)
            count+=1
    payload.append(register)
    root.append(type)
    root.append(payload)
    s = etree.tostring(root, pretty_print=True)
    print s
    file.write(s)
    file.close()
    
    

    
parser = argparse.ArgumentParser()

parser.add_argument('-u', action='store',dest='user',help='Username for Firewall API',default="admin")
parser.add_argument('-p', action='store',dest='passw',help='Password for Firewall API',default="panosqa")
parser.add_argument('-v', action='store',dest='vsys',help='vsys ID for IP Tags',default="vsys1")
parser.add_argument('-H', action='store',dest='host',help='Firewall IP',default="10.3.212.100")
parser.add_argument('-A', action='store',dest='action',help='register/unregister',default="register")
parser.add_argument('-i', action='store',dest='num',help='Number of IPs to Register/Unregister',default="10")
parser.add_argument('-s', action='store',dest='seed',help='RandomTag Seed',default="0")
parser.add_argument('-I', action='store',dest='ip',help='Ip Subnet to use',default="172.25.0.0/16")
parser.add_argument('-6', action='store',dest='ipv6',help='Is ipv6',default="no")

dagArr = parser.parse_args()
#xmlFile=dagArr.xml
hostIP=dagArr.host
username=dagArr.user
password=dagArr.passw
vsysID=dagArr.vsys
action=dagArr.action
numIps=dagArr.num
seed=dagArr.seed


v6=dagArr.ipv6
if(v6=='no'):
    mask=re.findall('/(\d+)',dagArr.ip)
    print mask
    if(int(mask[0])==24):
        ip=re.findall('(\d+.\d+.\d+).',dagArr.ip)
    elif(int(mask[0])==16):    
        ip=re.findall('(\d+.\d+).',dagArr.ip)
else:
    mask=[]
    mask.append(64)
    ip=unicode(dagArr.ip)
    print ip
    print type(ip)



if(action=='register'):
    genRegXML(numIps,seed,ip,v6,int(mask[0]))
    tmp='panxapi.py -xU uidreg.xml -h '+hostIP+' -l '+username+':'+password+' --vsys '+vsysID
    execShell(tmp)
elif(action=='unregister'):
    xmlFile=genUnregXML(numIps,seed,ip,v6,int(mask[0]))
    tmp='panxapi.py -xU uidunreg.xml -h '+hostIP+' -l '+username+':'+password+' --vsys '+vsysID
    execShell(tmp)    
else:
    print"Undefined Action - Script action can be only register or unregister"
