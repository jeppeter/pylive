#! python

import sys
import struct
import socket
import random


class RtpClient:
	def __init__(self,host,port,lport=None,pt=0x60):
		self.__host= host
		self.__port=port
		self.__sock = socket.socket(socket.AF_INET,socket.AF_DGRAM)
		if lport is None:
			random.seed(time.time())
			lport = random.randint(2000,30000)
		self.__sock.bind(('0.0.0.0',lport))
		self.__seq = 0
		self.__pt = pt
		return

	def __del__(self):
		self.__sock.close()
		del self.__sock
		self.__sock = None
		return

	def SendPacket(buf):
		buflen = len(buf)
		slen = 0

		while slen < buflen:
			curlen = buflen - slen
			if curlen > 1400:
				curlen = 1400
			# time stamp is 0
			smsg = struct.pack('>HHHH',(0x80<<8)|pt,self.__seq,0,0)
			smsg += buf[slen:(slen+curlen)]
			self.__seq += 1
			self.__sock.sendto(smsg,(self.__host,self.__port))
			slen += curlen
		return

class MediaFile(object):
 	def __init__(self,fi,startcode=None):
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
				idx = lastpack.find(self.__startcode,sidx)
				if idx != -1:
					eidx = idx
		ts = lastpack
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
			idx = ts.find(self.__startcode,sidx+len(self.__sidx))
			if idx != -1:
				eidx = idx
		return ts[:eidx],ts[eidx:]

def PSMediaFile(MediaFile):
	pass



				

		
