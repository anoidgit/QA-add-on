#-*-coding:utf-8-*-
import zmq
import subprocess,os,sys
import cv2
import urllib2,gzip
from StringIO import StringIO
from urllib import quote

globalStartupInfo = subprocess.STARTUPINFO()
globalStartupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

def runCmd(cmd):
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd(), shell=False, startupinfo=globalStartupInfo)
	p.wait()
	rs=p.stdout.read().decode()
	return rs

def capture(rsf):
	sdcardpath='/sdcard/screenshot.jpg'
	if os.path.exists(rsf):
		os.remove(rsf)
	jtcmd='adb.exe shell /system/bin/screencap -p '+sdcardpath
	runCmd(jtcmd)
	jtcmd='adb.exe pull '+sdcardpath+' '+rsf
	runCmd(jtcmd)
	jtcmd='adb.exe shell rm '+sdcardpath
	runCmd(jtcmd)

def segPic(srcf, rsf, startx, endx, starty, endy):
	image = cv2.imread(srcf)
	rs = image[startx:endx, starty:endy]
	cv2.imwrite(rsf, rs)

def getCon(addr):
	context = zmq.Context()
	socket = context.socket(zmq.REQ)
	socket.connect("tcp://"+addr)
	return socket

def touch(x, y):
	runCmd("adb.exe shell input tap "+str(x)+" "+str(y))

def ocr(addr, imgf):
	con = getCon(addr)
	con.send(imgf)
	rs = con.recv()
	return rs.decode("utf-8", "ignore")

def getHeader(urlstr):
	def getHost(urlstr):
		ind = urlstr.find("://")
		if ind >= 0:
			tmp = urlstr[ind + 3:]
		else:
			tmp = urlstr
		ind = tmp.find("/")
		if ind > 0:
			tmp = tmp[:ind]
		return tmp
	header = {
	"Host":getHost(urlstr),
	"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36",
	"DNT":"1",
	"Connection":"keep-alive",
	"Accept-Language":"zh-CN,zh;q=0.9",
	"Accept-Encoding":"gzip, deflate, br",
	"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
	}
	return header

def getPage(urlstr):
	header = getHeader(urlstr)
	req = urllib2.Request(urlstr, headers=header)
	r = urllib2.urlopen(req)
	rs = u""
	if r.info().get('Content-Encoding')=='gzip':
		buf = StringIO(r.read())
		f = gzip.GzipFile(fileobj = buf)
		rs = f.read()
		f.close()
	else:
		rs = r.read()
	r.close()
	return rs.decode("utf-8")

def getSougouPage(wd):
	return getPage("https://www.sogou.com/web?query="+quote(wd.encode("utf-8")))

def getSougouCount(wd):
	try:
		page = getSougouPage(wd)
		page = page[page.find(u"搜狗已为您找到")+8:]
		page = page[:page.find(u"条相关结果")]
		rs = int(page.replace(",", ""))
	except:
		rs = 0
	return rs + 1

def getKBPage(wd):
	def ready(strin):
		tmp = strin.split()
		rs = []
		for tmpu in tmp:
			if tmpu:
				rs.append(tmpu)
		return "+".join(rs)
	return getPage("http://47.100.22.113:20013/?inpage=1&p="+quote(ready(wd).encode("utf-8")))

def getKBCount(wd):
	try:
		page = getKBPage(wd)
		page = page[page.rfind(u"<div class=\"container\">"):]
		page = page[page.find("Output:"):]
		page = page[page.find("<br/><br/>")+10:]
		page = page[:page.find(" ")]
		rs = float(page)
	except:
		rs = 0.0
	return rs

def getCount(wd):
	#return getSougouCount(wd)
	return getKBCount(wd)

def cleanQ(strin, trimHead = True):
	if trimHead and len(strin)>1 and (strin[0].lower() in ["a", "b", "c", "d"]):
		tmp=strin[1:]
	else:
		tmp=strin
	return tmp.replace(" ", "")

def parseOCR(txtin):
	q = ""
	t = []
	tmp = txtin.split("\n")
	tmp1 = []
	for tmpu in tmp:
		tt = tmpu.strip()
		if tt:
			tmp1.append(tt)
	nline = len(tmp1)
	if nline < 4:
		tmp = tmp1[0].split()
		nd = len(tmp)
		ntotal = nd + nline - 1
		if ntotal < 4:
			t = tmp
			t.extend([tmp[-1] for i in xrange(3 - nline - nd)])
			t.extend(tmp1[1:])
			q = tmp[0]
		else:
			t = tmp[nd - 4 + nline:]
			t.extend(tmp1)
	else:
		t=tmp1[nline-4:]
		q="".join(tmp1[:nline-4])
	return q.replace(" ", ""), [cleanQ(tu, True) for tu in t]	

def choose(ans):
	lind={1:100, 2:200, 3:300, 4:400}
	rind={1:100, 2:200, 3:300, 4:400}
	touch(lind[ans], rind[ans])

def getAnswer(q, t):
	maxscore = 0
	ans = 1
	curid = 1
	for tu in t:
		qr = q+" "+tu
		print("Query "+str(curid)+" is "+qr)
		#curs = float(getCount(qr))/float(getCount(tu))
		curs = getCount(qr)
		print(">>Score of candidate "+str(curid)+": "+ str(curs))
		if curs > maxscore:
			maxscore = curs
			ans = curid
		curid += 1
	return ans

def main():
	run=True
	while run:
		cmd=raw_input(">>")
		if cmd.lower()=="exit":
			run=False
			break
		else:
			print(">>Getting screenshot")
			capture("screen.jpg")
			print(">>Focus on QA")
			segPic("screen.jpg", "center.jpg", 200, 1720, 0, 1080)
			print(">>run OCR")
			content = ocr("localhost:9355", "center.jpg")
			print(">>OCR result:")
			print(content)
			print(">>parsing OCR results")
			q, t = parseOCR(content)
			print(">>Question:")
			print(q)
			print(">>Query:")
			print(t)
			ans = getAnswer(q, t)
			print("Select "+str(ans))
			choose(ans)
			print("Done")

def testOCR():
	rs = ocr("localhost:9355", "test.jpg")
	print(type(rs))
	print(len(rs))
	print(rs.encode("gbk", "ignore"))
	with open("rec.txt", "w") as f:
		f.write(rs.encode("utf-8"))

def testCapture():
	capture("screen.jpg")

def testSeg():
	segPic("screen.jpg", "center.jpg", 120, 1800, 0, 1080)

def tesTouch():
	touch(360, 409)

def testPage():
	with open("test.html", "w") as f:
		f.write(getPage(u"百度云"))

def testCount():
	print(getCount(u"第一届奥斯卡 1981"))

if __name__ == "__main__":
	main()
