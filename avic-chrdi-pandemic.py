import requests
import re
import json
import base64
from PIL import Image
import io
import time
import os

def blackhole(avics,tkturl):
  success=True
  #下一行“XXXX”处配置4位职工编码，后面的状态默认为“全天在家”
  jsonstr='{"tablename":"staff_dailyhealthreport","columnArray":[{"columnName":"staff_code","columnValue":"XXXX"},{"columnName":"prop2","columnValue":"良好"},{"columnName":"prop3","columnValue":""},{"columnName":"prop4","columnValue":"无需隔离"},{"columnName":"prop5","columnValue":""},{"columnName":"prop6","columnValue":"已复工"},{"columnName":"prop7","columnValue":""},{"columnName":"prop8","columnValue":"天津"},{"columnName":"prop9","columnValue":""},{"columnName":"prop10","columnValue":"全天在家"},{"columnName":"prop11","columnValue":""},{"columnName":"prop12","columnValue":"无"}]}'
  payloadjson=json.loads(jsonstr)
  thisday=time.strftime('%d')
  oldday=thisday
  newday=False
  while success:
    if thisday!=oldday:
      newday=True
    if newday:
      print("newday!")
    else:
      print("not yet")
    chrdiapptktres=avics.get(tkturl,headers=chrdiappheader)
    print(chrdiapptktres.status_code)
    if chrdiapptktres.status_code==200:
      if newday:
        chrdiappsub=avics.post('https://chrdiapp.avic.com/mappers/operate_staffdaily/insertStaffdailyreport',json=payloadjson,headers=chrdiappheader)
        if chrdiappsub.status_code==200:
          print("submit ok!")
          newday=False
        else:
          success=False
          exit(0)
    else:
      success=False
      exit(0)
    oldday=thisday
    time.sleep(120)
    thisday=time.strftime('%d')
    print("today is"+thisday)
    print("refday is"+oldday)

def getQRCode(avics,appid):
  global header
  
  header['APP-ID']=appid
  qrcoderes=avics.get('https://sso.avic.com/sso/v2/qrcode/create',headers=header)
  qrjson=json.loads(qrcoderes.text)
  return avics,qrjson
 
 
def login(avics):
  chrdiapppage=avics.get("https://chrdiapp.avic.com/?ssoCompanyId=d831418ac8d940748edf06bc2280949f",headers=chrdiappheader,allow_redirects=False)
  loginpage=avics.get(chrdiapppage.headers["Location"],headers=header)
  validecoderes=avics.get('https://sso.avic.com/sso/validateCode',headers=header)
  appid=re.findall('appId.*;',loginpage.text)[0].split('"')[1]
  avics,qrjson = getQRCode(avics,appid)
  checkstr=qrjson['data']['qrCode']
  qrimgbase64=qrjson['data']['qrImg']
  qrbytes= base64.b64decode(qrimgbase64)
  qrimg = Image.open(io.BytesIO(qrbytes))
  qrimg.show()
  code=0
  payload = {"codeStr":checkstr}
  checkheader={
"Host": "sso.avic.com",
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0",
"Accept": "application/json, text/javascript, */*; q=0.01",
"Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
"Accept-Encoding": "gzip, deflate, br",
"Content-Type": "application/json",
"X-Requested-With": "XMLHttpRequest",
"Origin": "https://sso.avic.com",
"Connection": "keep-alive",
"Referer": "https://sso.avic.com/sso/login",
"Pragma": "no-cache",
"Cache-Control": "no-cache"}
  while code != 10000:
    time.sleep(1)
    checkres=avics.post('https://sso.avic.com/sso/qrcode/check',json=payload,headers=checkheader)
    checkjson=json.loads(checkres.text)
    code=checkjson['data']['status']
    print(code)
    if 10001 == code:
      print("请扫描二维码登录")
    elif 10002 == code:
      print("已扫描二维码，请在确认登录")
    elif 10000 == code:
      print("登录成功，正在跳转")
  pldstr=re.findall('execution" value=.*v2qrcode',loginpage.text)[0].split('"')
  pn1=pldstr[0]
  pn2=pldstr[6]
  pn3=pldstr[12]
  pn4=pldstr[16]
  pv1=pldstr[2]
  pv2=pldstr[8]
  pv3=checkstr
  pv4=pldstr[18]
  logindata={
          pn1:pv1,
          pn2:pv2,
          pn3:pv3,
          pn4:pv4
          }
  trueloginheader={
"Host": "sso.avic.com",
"Connection": "keep-alive",
"Upgrade-Insecure-Requests": "1",
"Origin": "https://sso.avic.com",
"Content-Type": "application/x-www-form-urlencoded",
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0",
"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
"Referer": "https://sso.avic.com/sso/login?service=https%3A%2F%2Foa.avic.com%2F",
"Accept-Encoding": "gzip, deflate, br",
"Accept-Language": "zh-CN,zh;q=0.9"
         }
  loginres=avics.post('https://sso.avic.com/sso/login',data=logindata,headers=trueloginheader,allow_redirects=False)
  tkturl=loginres.headers["Location"]
  blackhole(avics,tkturl)

avics=requests.Session()
header={"Host": "sso.avic.com",
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0",
"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
"Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
"Accept-Encoding": "gzip, deflate, br",
"Connection": "keep-alive",
"Upgrade-Insecure-Requests": "1",
"Pragma": "no-cache",
"Cache-Control": "no-cache"}
chrdiappheader={"Host": "chrdiapp.avic.com",
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0",
"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
"Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
"Accept-Encoding": "gzip, deflate, br",
"Connection": "keep-alive",
"Upgrade-Insecure-Requests": "1",
"Pragma": "no-cache",
"Cache-Control": "no-cache"}
login(avics)
