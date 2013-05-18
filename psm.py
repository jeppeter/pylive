#! python

import struct
import sys
import inspect
class XUnitException(Exception):
	def __init__(self,msg):
		t,v,tb = sys.exc_info()
		if isinstance(v,XUnitException) or issubclass(v.__class__,XUnitExxception):
			super(Exception,self).__init__(str(v))
		else:
			_f = inspect.stack()[1]
			_msg = '%s:%s (%s)(%s)'%(_f[1],_f[2],sys.exc_info(),msg)
			super(Exception,self).__init__(_msg)


def DecodePSM(psmcode):
	a = struct.unpack('>I',psmcode[:4])	
	sc = a[0]
	if sc != 0x1bc:
		return 
		#raise XUnitException('code %s (0x%x) is not 0x1bc'%(repr(psmcode[:4],sc)))
	a = struct.unpack('>H',psmcode[4:6])
	psmlen = a[0]
	if (len(psmcode)-6) < psmlen:
		raise XUnitException('length (%s) >= %d'%(repr(psmcode[4:6]),len(psmcode)))
	psmidicator = psmcode[6]
	markbit = psmcode[7]
	a = struct.unpack('>H',psmcode[8:10])
	infolen = a[0]
	if infolen > psmlen :
		raise XUnitException('%d >= psmlen %d'%(infolen,psmlen))
	ofs = 10+infolen
	descript = psmcode[10:ofs]
	a = struct.unpack('>H',psmcode[ofs:(ofs+2)])
	elmlen = a[0]
	if (elmlen + infolen) > psmlen:
		raise XUnitException('(elm %d) + (info %d) > (psm %d)'%(elmlen,infolen,psmlen))
	haslen = 0
	ofs += 2
	print('\tinfolen %d'%(infolen))
	print('\tofs %d (%s)'%(ofs,repr(descript)))
	while haslen < elmlen:
		a = struct.unpack('B',psmcode[ofs])
		stype = a[0]
		a = struct.unpack('B',psmcode[ofs+1])
		sid = a[0]
		a = struct.unpack('>H',psmcode[ofs+2:ofs+4])
		slen = a[0]
		sdesc = psmcode[ofs+4:ofs+4+slen]
		haslen += 4
		haslen += slen
		print('\tofs (0x%x)elmlen 0x%x haslen (0x%x) slen(0x%x) type 0x%x id 0x%x sdescr (%s)'%(ofs,elmlen,haslen,slen,stype,sid,repr(sdesc)))
		ofs += (4 + slen)
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




def DecodePSMFile(fname):
	mf = MediaFile(fname,'\x00\x00\x01\xbc')
	lpacket = ''
	roff = 0
	while True:
		spacket,lpacket = mf.GetPacket(lpacket)
		#logging.info('packet (%s) (%s)'%(spacket and len(spacket) or repr(spacket) , lpacket and len(lpacket) or repr(lpacket)))
		if  spacket is None or ( len(spacket) == 0 and lpacket is None)  :
			break
		sidx = spacket.find('\x00\x00\x01\xbc')
		if sidx == -1:
			roff += len(spacket)
			continue		
		eidx = spacket.find('\x00\x00\x01\xe0',sidx)
		rbuf = spacket[sidx:eidx]
		print('Parse PSM at 0x%08x'%(roff+sidx))
		DecodePSM(rbuf)
		print('\n\n')
		roff += len(spacket)
		
if __name__ == '__main__':
	DecodePSMFile(sys.argv[1])