import autorec
import os, sys, getopt, time, re, requests, json

import http.cookiejar
import http.cookiejar, requests.utils
import urllib3

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
import binascii

def usage():
    '--help'
    print("检查并更新cookies\
-f / --forced\t不管有没有过期都强制刷新(optional)")
    quit()

def getCorrespondPath(ts):
    '获取刷新地址'
    key = RSA.importKey('''\
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDLgd2OAkcGVtoE3ThUREbio0Eg
Uc/prcajMKXvkCKFCWhJYJcLkcM2DKKcSeFpD/j6Boy538YXnR6VhcuUJOhH2x71
nzPjfdTcqMz7djHum0qSZA0AyCBDABUqCrfNgCiJ00Ra7GmRj+YCK1NJEuewlb40
JNrRuoEUXpabUzGB8QIDAQAB
-----END PUBLIC KEY-----''')

    cipher = PKCS1_OAEP.new(key, SHA256)
    encrypted = cipher.encrypt(f'refresh_{ts}'.encode())
    return binascii.b2a_hex(encrypted).decode()

def cookie_dict2str(data:dict):
    'cookie_dict转换为字符串'
    s = ''
    for i in data.keys():
        s += "{}={};".format(i, data[i])
    return s

def refresh_cookies(is_forced=False):
    '刷新cookies'
        # 获取刷新地址
    ts = round(time.time() * 1000)
    correspondPath = getCorrespondPath(ts)

    # header和session
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0'
        }
    session = autorec.AutoRecSession()
    session.cookies = http.cookiejar.LWPCookieJar()
    session.cookies.load(filename='cookies.txt', ignore_discard=True, ignore_expires=True)
    cookies_dict = requests.utils.dict_from_cookiejar(session.cookies)

    # 检查是否需要更新
    if not is_forced:
        print("Checking cookies validity...")
        response = session.get(
            url='https://passport.bilibili.com/x/passport-login/web/cookie/info', 
            headers=headers, 
            params={'csrf':cookies_dict['bili_jct']}
            )
        data = response.json()['data']
        if data is None:
            print("Cookies invalid, try another set of cookies.txt and loginData.json instead.")
            return
        if data['refresh']:
            print("Cookies expired, refreshing...")
        else:
            ans = input("Cookies not expired, proceed refreshing?(Y/N): ")
            if ans.lower() != 'y':
                return

    # 获取refresh_csrf
    response = session.get(
        url="https://www.bilibili.com/correspond/1/{}".format(correspondPath), 
        headers=headers
        )
    try:
        refresh_csrf = re.search(r'(?<=<div id="1-name">).*?(?=</div>)', response.text).group()
    except AttributeError:
        print("Current cookies are invalid, try another set of cookies.txt and loginData.json instead.")
        return

    # 获取refresh_token
    with open("loginData.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    refresh_token = data['refresh_token']

    # 刷新cookies
    response = session.post(
        url='https://passport.bilibili.com/x/passport-login/web/cookie/refresh', 
        headers=headers, 
        params={
            'csrf': cookies_dict['bili_jct'], 
            'refresh_csrf': refresh_csrf, 
            'source': 'main_web',
            'refresh_token': refresh_token
            }
        )
    js = response.json()
    data = js['data']

    # 提取新的登录信息
    loginData = data

    # 提取新的csrf
    cookies_dict = requests.utils.dict_from_cookiejar(session.cookies)
    csrf = cookies_dict['bili_jct']

    # 确认更新
    print("Confirming cookies...")
    response = session.post(
        url='https://passport.bilibili.com/x/passport-login/web/confirm/refresh', 
        headers=headers, 
        params={
            'csrf': csrf, 
            'refresh_token': refresh_token
            }
        )
    code = response.json()['code']
    if code == 0:
        print("Cookies update success.")
    else:
        print("Cookies update failed:", response.json()['message'])
        return

    # 保存登录信息
    with open("loginData.json", 'w', encoding='utf-8') as f:
        json.dump(loginData, f)

    # 保存cookies
    session.cookies.save(filename='cookies.txt')
    new_cookies = cookie_dict2str(cookies_dict)[:-1] # 去除最后的分号

    # 更新blrec的cookies
    new_data = {"header": {"cookie": new_cookies}}
    session.set_blrec(new_data)

def main():
    # 初始化
    is_forced = False

    # 解析参数
    options, args = getopt.getopt(sys.argv[1:], "hf", ["help", "force"])
    for name, value in options:
        if name in ("-h","--help"):
            usage()
        if name in ("-f","--forced"):
            is_forced = True
    
    refresh_cookies(is_forced)

if __name__ == "__main__":
    main()
