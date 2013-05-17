#! python

import sys
import struct
import socket
import random
import time
import logging
class RtpClient:
	def __init__(self,host,port,lport=None,pt=0x60,scsr=None):
		self.__host= host
		self.__port=port
		self.__sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		random.seed(time.time())
		if lport is None:
			lport = random.randint(2000,30000)
		self.__scsr = scsr
		if scsr is None:
			self.__scsr = random.randint(0,0xffffffff)
		self.__sock.bind(('0.0.0.0',lport))
		self.__seq = 0
		self.__pt = pt
		return

	def __del__(self):
		self.__sock.close()
		del self.__sock
		self.__sock = None
		return

	def SendPacket(self,buf):
		buflen = len(buf)
		slen = 0

		while slen < buflen:
			curlen = buflen - slen
			if curlen > 1400:
				curlen = 1400
			# time stamp is 0
			smsg = struct.pack('>BBHII',0x80,self.__pt,self.__seq,0,self.__scsr)
			smsg += buf[slen:(slen+curlen)]
			self.__seq += 1
			self.__sock.sendto(smsg,(self.__host,self.__port))
			slen += curlen
		return


class MediaFile(object):
 	def __init__(self,fi,startcode):
 		if hasattr(fi,'read'):
			self.__fh = fi
		else:
			self.__fh = open(fi,'r+b')
		self.__startcode = startcode
		return

	def GetPacket(self,lastpack):
		'''
			return value is the packet buffer ,and the left packet
		'''
		if self.__startcode is None:
			raise Exception('Can not Packet in Base Class')
		sidx = -1
		eidx = -1
		if lastpack and len(lastpack) > 0:
			idx = lastpack.find(self.__startcode)
			if idx != -1:
				sidx = idx
				idx = lastpack.find(self.__startcode,sidx+len(self.__startcode))
				if idx != -1:
					eidx = idx
		ts = lastpack
		if ts is None:
			ts = ''
		while sidx == -1 :
			# we do not find the sidx
			cb = self.__fh.read((1<<20))
			if cb is None or len(cb) ==0 :
				return ts,None
			ts += cb
			idx = ts.find(self.__startcode)
			if idx != -1:
				sidx = idx
		while eidx == -1:
			cb = self.__fh.read((1<<20))
			if cb is None or len(cb) == 0:
				return ts,None
			ts += cb
			idx = ts.find(self.__startcode,sidx+len(self.__startcode))
			if idx != -1:
				eidx = idx
		if sidx == -1 or eidx == -1:
			return ts,None
		sbuf = ts[:eidx]
		lbuf = ts[eidx:]
		if len(lbuf) == 0 :
			lbuf += self.__fh.read(1<<20)
			if len(lbuf) == 0:
				lbuf = None
		return sbuf , lbuf

class PSMediaFile(MediaFile):
	pass


def SendFile(host,port,fname):
	rc = RtpClient(host,port)
	mf = PSMediaFile(fname,'\x00\x00\x01\xba')
	print('type of mf (%s)'%(mf.__class__))
	lpacket = ''
	while True:
		spacket,lpacket = mf.GetPacket(lpacket)
		#logging.info('packet (%s) (%s)'%(spacket and len(spacket) or repr(spacket) , lpacket and len(lpacket) or repr(lpacket)))
		if  spacket is None or ( len(spacket) == 0 and lpacket is None)  :
			break
		rc.SendPacket(spacket)
	return

if  __name__ ==  '__main__' :
	if len(sys.argv[1:]) < 3:
		sys.stderr.write('%s host port file\n'%(__file__))
		sys.exit(3)
	logging.basicConfig(level=logging.INFO,format="%(levelname)-8s [%(filename)-10s:%(funcName)-20s:%(lineno)-5s] %(message)s")
	print('%s\n'%(repr(sys.argv)))
	SendFile(sys.argv[1],int(sys.argv[2]),sys.argv[3])
		
