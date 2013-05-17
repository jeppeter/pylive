#! python

import socket
import sys
import select
import traceback
import inspect
import struct
import threading
import time
class XUnitException(Exception):
	def __init__(self,msg):
		t,v,tb = sys.exc_info()
		if isinstance(v,XUnitException) or issubclass(v.__class__,XUnitException):
			super(Exception,self).__init__(str(v))
		else:
			_f = inspect.stack()[1]
			_msg = '%s:%s (%s)(%s)'%(_f[1],_f[2],sys.exc_info(),msg)
			super(Exception,self).__init__(_msg)
gseq=0xffffff
isrunning=1

def rtpparser(rtpmsg):
	global gseq
	if len(rtpmsg) < 12:
		raise XUnitException('%s < 12'%(repr(rtpmsg)))
	pmsg = rtpmsg[:4]
	r , seq = struct.unpack('>HH',pmsg)
	if gseq > 0xffff:
		gseq = seq + 1
		sys.stderr.write('gseq %d seq %d\n'%(gseq ,seq))
	elif gseq != seq:
		sys.stderr.write('seq(%d) != gseq (%d)\n'%(seq,gseq))
		gseq = seq + 1
	else:
		gseq +=1
	if gseq > 0xffff:
		sys.stderr.write('\ngseq %d\n'%(gseq))
		gseq = 0
	rmsg = rtpmsg[12:]
	assert((len(rmsg) + 12)==len(rtpmsg))
	return rmsg


def InsertQueue(q,msg,lock):
	lock.acquire()
	q.append(msg)
	lock.release()
	return
	

def GetQueue(q,lock):
	r = None
	lock.acquire()
	if len(q) > 0:
		r = q[0]
		del q[0]
	lock.release()
	return r

def ReceiveRtp(sock,Q,lock):
	global isrunning
	while isrunning:
		try:
			rlist = [sock]
			wlist = []
			xlist = []
			ret = select.select(rlist,wlist,xlist,1)
			if len(ret) > 0 and len(ret[0]) > 0:
				#if True:
				msg,addr = sock.recvfrom(8192)
				if msg and len(msg) > 0:
					InsertQueue(Q,msg,lock)
		except :
			traceback.print_exc()
			isrunning = 0
			break
	return


'''
def DumpRtp(sock,fout):
	global isrunning
	l = 0
	wc = 0
	thr = None
	Q = []
	lock = threading.Lock()
	p = threading.Thread(target=ReceiveRtp,args=(sock,Q,lock))
	p.start()
	while isrunning:
		try:
			for i in xrange(wc):
				sys.stderr.write('\b')
			wc = 0
			msg= GetQueue(Q,lock)
			if msg is not None:
				rmsg = rtpparser(msg)
				fout.write(rmsg)
				l += len(rmsg)
				ws = 'len %d'%(l)
				wc = len(ws)
				sys.stderr.write(ws)
				sys.stderr.flush()
			else:
				time.sleep(0.1)
		except KeyboardInterrupt:
			break
		except :
			traceback.print_exc()
			break
	isrunning = 0
	while True:
		p.join(1)
		if not p.is_alive():
			break
	cnt = 0
	while True:
		msg = GetQueue(Q,lock)
		if msg is None:
			break
		for i in xrange(wc):
			sys.stderr.write('\b')
		wc = 0
		rmsg = rtpparser(msg)
		fout.write(rmsg)
		l += len(rmsg)
		ws = '[%d]len %d'%(cnt,l)
		wc = len(ws)
		sys.stderr.write(ws)
		sys.stderr.flush()
		cnt += 1
	sys.stderr.write('\n')	
	return l
'''

def DumpRtp(sock,fout):
	global isrunning
	l = 0
	bufsize = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
	sys.stderr.write('bufsize %d\n'%(bufsize))
	bufsize = 1 << 23
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,bufsize)
	bufsize = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
	sys.stderr.write('bufsize %d\n'%(bufsize))
	wc = 0
	ws = ''
	pnum = 0
	while isrunning:
		try:
			rlist = [sock]
			wlist = []
			xlist = []
			ret = select.select(rlist,wlist,xlist,0.5)
			if len(ret) > 0 and len(ret[0]) > 0:
				#if True:
				msg,addr = sock.recvfrom(8192)
				if msg is not None:
					rmsg = rtpparser(msg)
					fout.write(rmsg)
					l += len(rmsg)
					pnum += 1
					if (pnum % 100) == 0:
						if wc :
							for i in xrange(wc):
								sys.stderr.write('\b')
							wc = 0
						ws = '[%d] %d'%(pnum,l)
						wc = len(ws)
						sys.stderr.write(ws)
						sys.stderr.flush()
		except KeyboardInterrupt:
			isrunning = 0
			break
		except :
			traceback.print_exc()
			isrunning = 0
			break
	sys.stderr.write('\n')	
	return l



def ListenRtp(port):
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	sock.bind(('0.0.0.0',port))
	return sock

def Dump():
	sock = ListenRtp(int(sys.argv[1]))
	with open(sys.argv[2],'w+b') as fh:
		l = DumpRtp(sock,fh)
	sys.stderr.write('Dump %d\n'%(l))


if __name__ == '__main__':
	Dump()
