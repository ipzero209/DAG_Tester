#!/usr/bin/env python
import os, re, sys, traceback, pexpect, time
from panUtils import *

class Panfw_Cli():

    """ Class constructor """
    def __init__(self, user, host, passwd,logger=None):
        self.dict = {'user': user, \
                    'host': host, \
                    'passwd': passwd, \
                    'procid': None}
        #print "CLASS:::::"+debugFile
        self.logger=logger

    """ Function for SSH timeout """
    def _timeout_error(self, child):
        #print 'SSH could not login.  Timeout error.'
        #print child.before, child.after
        return None

    """ Function to start SSH """
    def _ssh_connect_admin(self):
        user = self.dict['user']
        host = self.dict['host']
        passwd = self.dict['passwd']
        output = ''
        #delete host file
        if os.path.exists('/root/.ssh/known_hosts'):
            os.remove('/root/.ssh/known_hosts')
        ssh_newkey = 'Are you sure you want to continue connecting'
        child = pexpect.spawn('ssh -l %s %s' % (user, host))
        i = child.expect([pexpect.TIMEOUT, ssh_newkey, '[p|P]assword: '])
        if i == 0: # Timeout
            return self._timeout_error(child)    
        if i == 1: # SSH does not have the public key. Just accept it.
            child.sendline ('yes')
            #child.expect ('[p|P]assword: ')
            i = child.expect([pexpect.TIMEOUT, '[p|P]assword:'])
            if i == 0: # Timeout
                #print child.before, child.after
                return self._timeout_error(child)
        child.sendline(passwd)
        i = child.expect([pexpect.TIMEOUT, '>', ']#'])
        if i == 0:
            return self._timeout_error(child)
        self.dict['procid'] = child

    """ Function to close SSH """
    def _ssh_disconnect(self):
        child = self.dict['procid']
        child.close(force=True)
        #print 'Just closed %s' % (child)


    """ Function to reset FPGA"""
    def _reset_fpga(self, commands):
        string = ''
        child = self.dict['procid']
        for command in commands:
            output = ''
            child.sendline(command)
            while True:
                i = child.expect([pexpect.TIMEOUT, '\W*.*\n+', ']#\s*', 'pdt>\s*'])
                if i == 0: #Timeout
                    #return self._timeout_error(child)
                    break
                if i == 1:
                    output += child.after
                if i == 2:
                    output += child.after
                    time.sleep(2)
                    break
                if i == 3:
                    output += child.after
                    time.sleep(2)
                    break
            string += output
            #print string
            #print 'just sent command',command
        self.dict['procid'] = child
        return string


    """ Function to send a list of CLI commands and return output for all commands """
    def _send_cli_command(self, commands):
        string = ''
        child = self.dict['procid']
        for command in commands:
            output =''
            child.sendline(command)
            child.timeout=0.1
            time.sleep(0.25)
            while True:
                i = child.expect([pexpect.TIMEOUT, \
                			'\W+.*?Please type "y" for yes or "n" for no\s*', \
                            '\W*.*\(y\ or\ n\)\s*', \
                            '\W*.*lines\ +\d+\-\d+', \
                            '\W*.*more.*',\
                            '\W*\[edit\]\s*',\
                            '\W*\@.*[>#]\s*', \
                            '\W+.*\s+', \
                            '\.\.', \
                            pexpect.EOF])
		#print i
                if i == 0: 
		    #print "Error"
		    #Timeout
                    #return self._timeout_error(child)
                    break
                if i == 1 or i == 2:
                    #print "dydsfsdfsfdsf"
                    time.sleep(2)
                    output += child.after
                    child.sendline('y')
                    pass
                if i == 3:
                    output += child.after
                    child.sendline(' ')
                    pass
                if i == 4:
                    output += child.after
                    child.sendline(' ')
                    pass
                if i == 5:
                    output += child.after
                    pass
                if i == 6:
                    output += child.after
                    break
                if i == 7:
                    output += child.after
                    pass
                if i == 8:
                    output += child.after
                    pass
                if i == 9:
                    output += child.before
                    break
            string += output
            #print string
        self.dict['procid'] = child
        return string

    """ Function to find currently installed build.
        if found build, return build version, else, return 0 """
    def _cli_find_installed_build(self):
        output = ''
        child = self.dict['procid']
        '''i = child.expect([pexpect.TIMEOUT, '>'])
        if i == 0:
            return self._timeout_error(child)'''
        child.sendline('show system info | match sw-version')
        while True:
            i = child.expect([pexpect.TIMEOUT, \
                            '\W*.*lines\ +\d+\-\d+', \
                            '\W*.*\s+', \
                            '>\s*'])
            if i == 0: #Timeout
                break
            if i == 1:
                output += child.after
                child.sendline(' ')
            if i == 2:
                output += child.after
            if i == 3:
                break
        self.dict['procid'] = child
        #build = re.search('(\d+\.\d+\.\d+\-\w+)', output)
        build = re.search('(\d+\.\d+\.\d+\-?\w?\d?\d?\d?)', output)
        if(build):
            return build.group(0)
        else:
            return 0
    
    """ Function to find latest build from upgrade server.
        if found, return build version.  else, return 0 """
    def _cli_find_avail_build(self):
        output = ''
        found = 0
        child = self.dict['procid']
        '''i = child.expect([pexpect.TIMEOUT, '>'])
        if i == 0:
            return self._timeout_error(child)'''
        child.sendline('request system software check')
        while True:
            i = child.expect([pexpect.TIMEOUT, \
                            '\W*.*lines\ +\d+\-\d+', \
                            '\W*.*\s+', \
                            '>\s*'])
            if i == 0: #Timeout
                break
            if i == 1:
                output += child.after
                child.sendline(' ')
            if i == 2:
                output += child.after
            if i == 3:
                break
        self.dict['procid'] = child
        output_list = output.split('\n')
        for i in range(0,len(output_list)-1):
            build = re.search('(\d+\.\d+\.\d+\-?\w?\d?\d?\d?)', output_list[i])
            if(build):
                return build.group(0)
        return 0

    """ Function to find match.  If match return 1, else return 0 """
    def _cli_find_match(self, output, pattern):
        output_list = output.split('\n')
        for i in range(0,len(output_list)-1):
            match = re.search(pattern, output_list[i])
            if(match):
                return 1
            else:
                return 0

    """ Function to find job id """
    def _cli_find_jobid(self, output):
        id = re.search('jobid\ (\d+)', output)
        if(id):
            id1 = re.search('\d+',id.group(0))
            return id1.group(0)
        else:
            return 0
            
    """ Function to follow status of job id """
    def _cli_mon_jobid(self, id):
        sleep_time = 10
        iteration = 8640
        
        child = self.dict['procid']
        for a in range(0, iteration):
            output = ''
            child.sendline('show jobs id ' + str(id))
            while True:
                i = child.expect([pexpect.TIMEOUT, \
                                '\W*.*lines\ +\d+\-\d+', \
                                '\W*.*\s+', \
                                '>\s*'])
                if i == 0: #Timeout
                    break
                if i == 1:
                    output += child.after
                    child.sendline(' ')
                    #print output
                if i == 2:
                    output += child.after
                    #print output
                if i == 3:
                    break
            pattern = re.search('(FIN)', output)
            if(pattern):
                pattern1 = re.search('(FIN\s*OK)', output)
                if(pattern1):
                    #print output
                    time_stamp=re.findall('(\d+:\d+:\d+)',output)
                    #print time_stamp
                    res = 1
                else:
                    #print output
                    time_stamp=re.findall('(\d+:\d+:\d+)',output)
                    #print time_stamp
                    res = 0
                break
            else:
                res = 0
            time.sleep(sleep_time)
            sleep_time+=5
        self.dict['procid'] = child
        return res,(time_stamp[0],time_stamp[2])
        
    """ Function to check Auto Commit success after bootup """
    def _cli_check_autocommit(self):
        res = self._cli_mon_jobid(1)
        if(res == 1):
            return res
        else:
            return 0
        
    """ Function to check that all system softwares are up """
    def _cli_check_system_software(self):
        err = ['stop', 'fail']        
        child = self.dict['procid']
        output = ''        
        str = ''
        res = 0
        child.sendline('show system software status')
        while True:
            i = child.expect([pexpect.TIMEOUT, \
                            '\W*.*lines\ +\d+\-\d+', \
                            '\W*.*\s+', \
                            '>\s*'])
            if i == 0: #Timeout
                break
            if i == 1:
                output += child.after
                output += child.before
                child.sendline(' ')
            if i == 2:
                output += child.after
            if i == 3:
                break
            #print output
        for a in range(0, len(err)):
            pattern = re.search(err[a], output)
            if(pattern):
                res = 1
                str += err[a]
                break
        self.dict['procid'] = child
        if(res == 0):
            return res
        else:
            #return str
            return res
        
    """ Function to check status of "show management-clients" """
    def _cli_check_management_clients(self):
        '''err = ['stop', 'fail']        
        child = self.dict['procid']
        str = ''
        res = 0'''
        output = self._send_cli_command(['show management-clients'])
        '''for a in range(0, len(err)):
            pattern = re.search(err[a], output)
            if(pattern):
                res = 1
                str += err[a]
        self.dict['procid'] = child
        if(res == 0):
            return res
        else:
            return str'''

    def _ping_test(self, ip):
        test_pass = 0
        command = "ping -c 4 %s" % (ip)
        child = pexpect.spawn(command)
        i = child.expect([pexpect.TIMEOUT, '0%', '25%', '50%', '75%', '100%', pexpect.EOF])
        while True:
            if(i == 0 or i == 4 or i == 5):
                test_pass = 0
                #print 'Ping to %s ',ip,' failed.'
                break
            if(i == 1 or i == 2 or i == 3):
                #print child.before, child.after
                test_pass = 1
                #print 'Ping to %s ',ip,' passed.'
                break
            #if(i == 6):
                #print child.before, child.after
        return test_pass


    """ Class destructor """
    def _delete_object(self):
        del self
        #print 'Just deleted object'

