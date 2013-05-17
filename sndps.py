#! python

import socket
import struct
import sys
import time
def SendFile(sock,host,port,fname):
	pnum = 0
	with open(fname,'rb') as f:
		while True:
			msg = f.read(1400)
			if (pnum % 10) == 0:			
				#time.sleep(0.01)
				pass
			if msg is None or len(msg) == 0:
				break
			mhdr = struct.pack('>HH',0,pnum)
			mhdr += ' '*8
			mhdr += msg
			sock.sendto(mhdr,(host,port))
			pnum += 1
			if pnum > 0xffff:
				pnum = 0
	return		

def BindUdp(port):
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	sock.bind(('0.0.0.0',port))
	return sock

def sendfile():
	sock = BindUdp(int(sys.argv[4]))
	SendFile(sock,sys.argv[1],int(sys.argv[2]),sys.argv[3])

if __name__ == '__main__':
	sendfile()
