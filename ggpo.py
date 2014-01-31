#!/usr/bin/python

# very rudimentary ggpo command line client
# protocol reverse engineered from the official adobe air client
# (c) 2014 Pau Oliva Fora

import socket
import string
import re
import sys
import signal
from subprocess import call

USERNAME="pof"
PASSWORD="XXXXXXXX"
CHANNEL="ssf2t"

DEBUG=0 # values: 0,1,2
TIMEOUT=3

SPECIAL=""
OLDDATA=""

GRAY = '\033[0;30m'
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
BLUE = '\033[0;34m'
MAGENTA = '\033[0;35m'
CYAN = '\033[0;36m'

B_GRAY = '\033[1;30m'
B_RED = '\033[1;31m'
B_GREEN = '\033[1;32m'
B_YELLOW = '\033[1;33m'
B_BLUE = '\033[1;34m'
B_MAGENTA = '\033[1;35m'
B_CYAN = '\033[1;36m'

END = '\033[0;m'

def interrupted(signum, frame):
	"called when read times out"
	#print 'interrupted!'
signal.signal(signal.SIGALRM, interrupted)

def input():
	try:
		#print "> ",
		foo = sys.stdin.readline()
		foo = foo.strip(' \t\n\r')
		return foo
	except:
		# timeout
		return

def readdata():
	global s
	try:
		foo = s.recv(4096)
		return foo
	except:
		return

def pad(value,length=4):
	l = len(value)
	while (l<length):
		value="\x00" + value
		l = len(value)
	return value

def parse(cmd):
	global SPECIAL

	pdulen = int(cmd[0:4].encode('hex'), 16)
	action = cmd[4:8]

	# chat
	if (action == "\xff\xff\xff\xfe"):
		nicklen = int(cmd[8:12].encode('hex'),16)
		nick = cmd[12:12+nicklen]
		msglen = int(cmd[12+nicklen:12+nicklen+4].encode('hex'),16)
		msg = cmd[12+nicklen+4:pdulen+4]
		print CYAN + "<" + str(nick) + "> " + END + str(msg)

	# state changes (away/available/playing)
	elif (action == "\xff\xff\xff\xfd"):

		unk1 = cmd[8:12]
		unk2 = cmd[12:16]

		nicklen = int(cmd[16:20].encode('hex'),16)
		nick = cmd[20:20+nicklen]


		if (unk1 == "\x00\x00\x00\x01" and unk2 == "\x00\x00\x00\x00"): print GRAY + "-!- " + B_GRAY + str(nick) + GRAY +" has quit" + END

		#if (unk1 == "\x00\x00\x00\x03" and unk2 == "\x00\x00\x00\x00"):
		#if (unk1 == "\x00\x00\x00\x03" and unk2 == "\x00\x00\x00\x01"):
		#if (unk1 == "\x00\x00\x00\x04" and unk2 == "\x00\x00\x00\x01"): # match ended?
		#if (unk1 == "\x00\x00\x00\x05" and unk2 == "\x00\x00\x00\x01\):

		elif ((unk1 == "\x00\x00\x00\x01" and unk2 == "\x00\x00\x00\x01") or (unk1 == "\x00\x00\x00\x02" and unk2 == "\x00\x00\x00\x01")):

			state = int(cmd[20+nicklen:20+nicklen+4].encode('hex'),16)  # 1=away, 0=back, 2=play

			if (state==2):
				nick2len = int(cmd[24+nicklen:28+nicklen].encode('hex'),16)
				nick2 = cmd[28+nicklen:28+nicklen+nick2len]

				print MAGENTA + "-!- new match " + B_MAGENTA + str(nick) + MAGENTA + " vs " + B_MAGENTA + str(nick2) + END

			elif (state <2):
				unk4 = cmd[20+nicklen+4:20+nicklen+8]

				iplen = int(cmd[20+nicklen+8:20+nicklen+12].encode('hex'),16)
				ip = cmd[32+nicklen:32+nicklen+iplen]

				unk6 = cmd[32+nicklen+iplen:32+nicklen+iplen+4]
				unk7 = cmd[36+nicklen+iplen:36+nicklen+iplen+4]

				citylen = int(cmd[40+nicklen+iplen:44+nicklen+iplen].encode('hex'),16)
				city = cmd[44+nicklen+iplen:44+nicklen+iplen+citylen]

				cclen = int(cmd[44+nicklen+iplen+citylen:48+nicklen+iplen+citylen].encode('hex'),16)
				cc = cmd[48+nicklen+iplen+citylen:48+nicklen+iplen+citylen+cclen]

				countrylen = int(cmd[48+nicklen+iplen+citylen+cclen:48+nicklen+iplen+citylen+cclen+4].encode('hex'),16)
				country = cmd[52+nicklen+iplen+citylen+cclen:52+nicklen+iplen+citylen+cclen+countrylen]

				print GRAY + "-!- " + B_GRAY + str(nick) + GRAY + "@" + str(ip),
				if (city != "" and cc != ""): print "(" + city + ", " + cc + ")",
				elif (city == "" and cc != ""): print "(" + cc + ")",
				if (state == 0): print "is available",
				if (state == 1): print "is away",
				print END

		else:
			if (DEBUG==1): print BLUE + "ACTION: " + repr(action) + " + DATA: " + repr(cmd[8:pdulen+4]) + END

	# challenge
	elif (action == "\xff\xff\xff\xfc"):

		nicklen = int(cmd[8:12].encode('hex'),16)
		nick = cmd[12:12+nicklen]

		channellen = int(cmd[12+nicklen:12+nicklen+4].encode('hex'),16)
		channel = cmd[16+nicklen:16+nicklen+channellen]

		print RED + "INCOMING CHALLENGE FROM " + str(nick) + " @ " + channel + END

	# cancel challenge
	elif (action == "\xff\xff\xff\xef"):

		nicklen = int(cmd[8:12].encode('hex'),16)
		nick = cmd[12:12+nicklen]

		print YELLOW + "CANCEL CHALLENGE " + str(nick) + END


	elif (action == "\xff\xff\xff\xff"):
		print GRAY + "-!- Connection established" + END

	# watch
	elif (action == "\xff\xff\xff\xfa"):

		nick1len = int(cmd[8:12].encode('hex'),16)
		nick1 = cmd[12:12+nick1len]
		nick2len = int(cmd[12+nick1len:16+nick1len].encode('hex'),16)
		nick2 = cmd[16+nick1len:16+nick1len+nick2len]

		print GRAY + "> watch " + nick1 + " vs " + nick2 + END

		quark = cmd[20+nick1len+nick2len:pdulen+4]
		args = ['/opt/ggpo/ggpofba.exe', quark]
		call(args)

		#\x00\x00\x00[\xff\xff\xff\xfa\x00\x00\x00\x0fsmoothmacgroove\x00\x00\x00\x07manelxd\x00\x00\x005quark:stream,ssf2t,challenge-06228-1391119057.75,7000

	# unknown action
	else:
		if (SPECIAL == "" ):
			if (DEBUG==1): print BLUE + "ACTION: " + repr(action) + " + DATA: " + repr(cmd[8:pdulen+4]) + END
		else:
			parsespecial(cmd)

	#print ("PDULEN: " + str(pdulen) + " ACTION: " + str(action))
	#print ("PDULEN: " + str(pdulen) + " CMDLEN: " + str(len(cmd)))
	if ( len(cmd) > pdulen+4 ): 
		parse(cmd[pdulen+4:])
		

def parsespecial(cmd):
	global SPECIAL

	pdulen = int(cmd[0:4].encode('hex'), 16)
	#myseqnum = int(cmd[4:8].encode('hex'),16)

	if (SPECIAL=="INTRO"):
		channellen = int(cmd[12:12+4].encode('hex'),16)
		channel = cmd[16:16+channellen]

		topiclen = int(cmd[16+channellen:20+channellen].encode('hex'),16)
		topic = cmd[20+channellen:20+channellen+topiclen]

		msglen = int(cmd[20+channellen+topiclen:24+channellen+topiclen].encode('hex'),16)
		msg = cmd[24+channellen+topiclen:24+channellen+topiclen+msglen]

		print "\n" + B_GREEN + str(channel) + GREEN + " || " + B_GREEN + str(topic) + GREEN
		print str(msg) + END
		SPECIAL=""

	elif (SPECIAL=="AWAY"):
		SPECIAL=""

	elif (SPECIAL=="BACK"):
		SPECIAL=""

	elif (SPECIAL=="LIST"):
		SPECIAL=""
		parselist(cmd)

	elif (SPECIAL=="USERS"):
		SPECIAL=""
		parseusers(cmd)

	else:
		if (DEBUG==1): print BLUE + "SPECIAL=" + SPECIAL + " + DATA: " + repr(cmd[8:pdulen+4]) + END

def parseusers(cmd):

	global SPECIAL, OLDDATA
	pdulen = int(cmd[0:4].encode('hex'), 16)

	## ugly workaround for when the user list is splitted in 2 PDUs
	#print "PDULEN: " + str(pdulen) + " CMDLEN: " + str(len(cmd))
	if (len(cmd)!=pdulen+4 and OLDDATA==""):
		SPECIAL="USERS"
		OLDDATA=cmd
		return

	if (OLDDATA!=""):
		cmd = OLDDATA + cmd
		pdulen = int(cmd[0:4].encode('hex'), 16)
		OLDDATA=""
		SPECIAL=""
	## end of workaround

	print YELLOW + "-!- user list:" + END

	i=16
	while (i<pdulen):
	#while (i<len(cmd)-4):

		len1 = int(cmd[i:i+4].encode('hex'),16)
		i=i+4
		nick = cmd[i:i+len1]
		i=i+len1

		status = int(cmd[i:i+4].encode('hex'),16)  # 1=away, 2=playing, 0=available?
		i=i+4

		p2len = int(cmd[i:i+4].encode('hex'),16)  # should be 0 when not playing
		i=i+4

		if (p2len > 0):
			p2nick = cmd[i:i+p2len]
			i=i+p2len

		iplen = int(cmd[i:i+4].encode('hex'),16)
		i=i+4

		ip = cmd[i:i+iplen]
		i=i+iplen

		unk1 = cmd[i:i+4]
		i=i+4

		unk2 = cmd[i:i+4]
		i=i+4

		citylen = int(cmd[i:i+4].encode('hex'),16)
		i=i+4

		city = cmd[i:i+citylen]
		i=i+citylen

		cclen = int(cmd[i:i+4].encode('hex'),16)
		i=i+4

		cc = cmd[i:i+cclen]
		i=i+cclen

		countrylen = int(cmd[i:i+4].encode('hex'),16)
		i=i+4

		country = cmd[i:i+countrylen]
		i=i+countrylen

		unk3 = cmd[i:i+4]
		i=i+4

		print YELLOW + "-!- " + B_GRAY + str(nick) + GRAY + "@" + str(ip),
		if (city != "" and cc != ""): print "(" + city + ", " + cc + ")",
		elif (city == "" and cc != ""): print "(" + cc + ")",
		if (status == 0): print "is available",
		if (status == 1): print "is away",
		if (status == 2): print "is playing against " + B_GRAY + p2nick,
		print END

	print YELLOW + "-!- EOF user list." + END


def parselist(cmd):

	global SPECIAL, OLDDATA
	pdulen = int(cmd[0:4].encode('hex'), 16)

	## ugly workaround for when the channel list is splitted in 2 PDUs
	print "PDULEN: " + str(pdulen) + " CMDLEN: " + str(len(cmd))
	if (len(cmd)!=pdulen+4 and OLDDATA==""):
		SPECIAL="LIST"
		OLDDATA=cmd
		return

	if (OLDDATA!=""):
		cmd = OLDDATA + cmd
		pdulen = int(cmd[0:4].encode('hex'), 16)
		OLDDATA=""
		SPECIAL=""
	## end of workaround

	print YELLOW + "-!- channel list:" + END

	i=12
	while (i<pdulen):
	#while (i<len(cmd)-4):
		#num = int(cmd[i:i+4].encode('hex'),16)
		i=i+4
		len1 = int(cmd[i:i+4].encode('hex'),16)
		i=i+4
		name1 = cmd[i:i+len1]
		i=i+len1
		len2 = int(cmd[i:i+4].encode('hex'),16)
		i=i+4
		name2 = cmd[i:i+len2]
		i=i+len2
		len3 = int(cmd[i:i+4].encode('hex'),16)
		i=i+4
		name3 = cmd[i:i+len3]
		i=i+len3
		print YELLOW + "-!- " + B_GRAY +  str(name1) + GRAY + " (" + str(name2) + ") -- " + str(name3)

	print YELLOW + "-!- EOF channel list." + END

if __name__ == '__main__':

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(('ggpo.net', 7000))

	# welcome packet (?)
	s.send('\x00\x00\x00\x14\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1d\x00\x00\x00\x01')

	# authentication
	sequence=0x2
	pdulen = 4 + 4 + 4 + len(USERNAME) + 4 + len (PASSWORD) + 4
	s.send( pad(chr(pdulen)) + "\x00\x00\x00\x02" + "\x00\x00\x00\x01" + pad(chr(len(USERNAME))) + USERNAME + pad(chr(len(PASSWORD))) + PASSWORD + "\x00\x00\x17\x79")
	sequence=sequence+1

	# choose channel
	channellen = len(CHANNEL)
	pdulen = 4 + 4 + 4 + channellen
	s.send( pad(chr(pdulen)) + pad(chr(sequence)) + "\x00\x00\x00\x05" + pad(chr(channellen)) + CHANNEL )
	sequence=sequence+1

	# start away by default
	s.send( pad(chr(12)) + pad(chr(sequence)) + "\x00\x00\x00\x06" + "\x00\x00\x00\x01")
	sequence=sequence+1

	while 1:
		# set alarm
		signal.alarm(TIMEOUT)
		line = input()
		# disable the alarm after success
		signal.alarm(0)

		if (line != None and not line.startswith("/")):
			#print line
			msglen = len(line)
			pdulen = 4 + 4 + 4 + msglen
			# [ 4-byte pdulen ] [ 4-byte sequence ] [ 4-byte command ] [ 4-byte msglen ] [ msglen-bytes msg ]
			s.send( pad(chr(pdulen)) + pad(chr(sequence)) + "\x00\x00\x00\x07" + pad(chr(msglen)) + line)
			sequence=sequence+1

		# send a challenge request
		if (line != None and line.startswith("/challenge ")):
			nick = line[11:]
			nicklen = len(nick)
			pdulen = 4 + 4 + 4 + nicklen + 4 + channellen
			s.send( pad(chr(pdulen)) + pad(chr(sequence)) + "\x00\x00\x00\x08" + pad(chr(nicklen)) + nick + pad(chr(channellen)) + CHANNEL)
			sequence=sequence+1

		# cancel an ongoing challenge request
		if (line != None and line.startswith("/cancel ")):
			nick = line[8:]
			nicklen = len(nick)
			pdulen = 4 + 4 + 4 + nicklen
			s.send( pad(chr(pdulen)) + pad(chr(sequence)) + "\x00\x00\x00\x1c" + pad(chr(nicklen)) + nick )
			sequence=sequence+1

		# watch an ongoing match
		if (line != None and line.startswith("/watch ")):
			nick = line[7:]
			nicklen = len(nick)
			pdulen = 4 + 4 + 4 + nicklen
			s.send( pad(chr(pdulen)) + pad(chr(sequence)) + "\x00\x00\x00\x10" + pad(chr(nicklen)) + nick )
			sequence=sequence+1

		# set away status (can't be challenged)
		if (line == "/away"):
			pdulen = 4+4+4
			SPECIAL="AWAY"
			s.send( pad(chr(pdulen)) + pad(chr(sequence)) + '\x00\x00\x00\x06' + '\x00\x00\x00\x01')
			sequence=sequence+1

		# return back from away (can be challenged)
		if (line == "/back"):
			pdulen = 4+4+4
			SPECIAL="BACK"
			s.send( pad(chr(pdulen)) + pad(chr(sequence)) + '\x00\x00\x00\x06' + '\x00\x00\x00\x00')
			sequence=sequence+1

		# view channel intro
		if (line == "/intro"):
			pdulen = 4+4
			SPECIAL="INTRO"
			s.send( pad(chr(pdulen)) + pad(chr(sequence)) + '\x00\x00\x00\x02')
			sequence=sequence+1

		# list channels
		if (line == "/list"):
			pdulen = 4+4
			SPECIAL="LIST"
			s.send( pad(chr(pdulen)) + pad(chr(sequence)) + '\x00\x00\x00\x03')
			sequence=sequence+1

		# list users
		if (line == "/users"):
			pdulen = 4+4
			SPECIAL="USERS"
			s.send( pad(chr(pdulen)) + pad(chr(sequence)) + '\x00\x00\x00\x04')
			sequence=sequence+1

		if (line == "/quit"):
			s.close()
			sys.exit(0)

		signal.alarm(TIMEOUT)
		data = readdata()
		signal.alarm(0)
		if not data: continue

		if (DEBUG>1):
			print BLUE + "HEX: ",repr(data) + END

		parse(data)

	s.close()
