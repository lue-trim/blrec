import os, time, requests, re, json, toml, multiprocessing, traceback, datetime
import http.cookiejar, requests.utils
import urllib3

from urllib.parse import unquote, quote
from http.server import HTTPServer, BaseHTTPRequestHandler

# classes
class RequestHandler(BaseHTTPRequestHandler):
    '网络请求服务器'
    def do_POST(self):
        '接收到POST信息时'
        # 读取参数
        data = self.rfile.read(int(self.headers['content-length']))
        data = unquote(str(data, encoding='utf-8'))
        json_obj = json.loads(data)
        event_type = json_obj['type']

        # 根据接收到的blrec webhook参数执行相应操作
        # 更新：不用套try语句，要是出错http模块会自己处理
        if event_type == 'RecordingFinishedEvent':
            # 录制完成，更新cookies
            refresh_cookies()
        elif event_type == 'VideoPostprocessingCompletedEvent':
            # 视频后处理完成，上传到alist

            # 获取直播间信息
            room_id = json_obj['data']['room_id']
            session = AutoRecSession()
            room_info = session.get_blrec_data(room_id)

            # 上传
            filename = json_obj['data']['path']
            upload_video(filename, room_info)
        else:
            print("Got new Event: ", event_type)
        
        # 回复
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        data = {
            "code": 200,
            "message": "Mua!"
        }
        self.wfile.write(str(data).encode())

class File:
    '表单上传用文件类'
    # 注：with open()语句一定要写在class外面，否则对文件操作符开关过于频繁容易导致报错
    def __init__(self, fp, filename):
        self.filename = filename
        self.fp = fp
        self.total_size = os.path.getsize(self.filename)
        self.current_size = 0
        self.last_time = datetime.datetime.now()

    def get_size(self):
        '获取文件大小'
        return self.total_size

    def read(self, size=-1):
        'read方法，给http模块调用，让其对文件自动分片'
        #with open(self.filename, 'rb') as file:
        #chunk_size = 10000
        #if self.get_size() <= chunk_size:
            # 小文件直接上传
            #return self.fp.read(self.get_size())
        #else:
            # 大文件分片上传

        # 识别chunk size
        if size == -1:
            self.current_size = self.total_size
        elif size >= self.total_size:
            self.current_size += self.total_size - self.current_size
        else:
            self.current_size += size

        # 计算上传时间
        new_time = datetime.datetime.now()
        delta_time = new_time - self.last_time
        secs = delta_time.total_seconds()
        if secs <= 0:
            secs = 1.0
        self.last_time = new_time

        # 输出进度并返回
        print("Read: {:.2f}%, {:.2f}kB/s".format(
            self.current_size / self.total_size * 100,
            self.current_size / secs / 1024
        ),
        end='          \r')
        return self.fp.read(size)

    def __len__(self):
        '获取文件大小，给http模块调用'
        return self.get_size()

class AutoRecSession(requests.Session):
    '本地http通信专用类'
    def get_alist_token(self):
        '获取alist管理token'
        url = "http://{}:{}{}".format(host_alist, port_alist, '/api/auth/login/hash')
        params = {
            "username": username,
            "password": password.lower()
        }
        headers = {
            'Content-Type': 'application/json'
        }

        # 请求API
        data = utils.dict2str(params)
        response = self.post(url, data=data, headers=headers)
        response_json = response.json()
        # 获取结果
        if response_json['code'] == 200:
            print("Get token success.")
            return response_json['data']['token']
        else:
            print("Get token failed,", response_json['message'])
            return ""
    
    def copy_alist(self, token:str, source_dir:str, filenames:list, dist_dir:str):
        '复制文件'
        # 请求参数
        url = "http://{}:{}{}".format(host_alist, port_alist, '/api/fs/copy')
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        data = {
            "src_dir": source_dir,
            "dst_dir": dist_dir,
            "names": filenames
        }

        # 请求API
        response = self.post(url=url, data=utils.dict2str(data), headers=headers)
        data = response.json()

        # 获取结果
        if data['code'] == 200:
            print("Copy success.")
        else:
            print("Copy failed,", data['message'])
        
        return data['code']
    
    def rm_alist(self, token:str, dirname:str, filenames:list):
        '删除文件'
        # 请求参数
        url = "http://{}:{}{}".format(host_alist, port_alist, '/api/fs/remove')
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        data = {
            "dir": dirname,
            "names": filenames
        }

        # 请求API
        response = self.post(url=url, data=utils.dict2str(data), headers=headers)
        data = response.json()

        # 获取结果
        if data['code'] == 200:
            print("Remove success:", dirname, filenames)
        else:
            print("Remove failed:", dirname, filenames, data['message'])
        
        return data['code']

    def upload_alist_action(self, token:str, local_filename:str, dist_filename:str):
        '供multiprocessing使用的流式上传文件，自动重试6次以防上传时网盘抽风'
        for i in range(6):
            try:
                self.upload_alist(token, local_filename, dist_filename, True)
            except:
                traceback.print_exc()
                time.sleep(4**i)
            else:
                break

    def upload_alist(self, token:str, filename:str, dist_filename:str, remove_after_upload=False):
        '流式上传文件'
        dist_filename = quote(dist_filename) # URL编码

        # 请求参数
        url = "http://{}:{}{}".format(host_alist, port_alist, '/api/fs/put')
        headers = {
            "Authorization": token,
            "File-Path": dist_filename,
            "As-Task": "True",
            "Content-Type": "application/octet-stream",
        }

        # 打开文件
        with open(filename, 'rb') as f:
            data = File(f, filename)
            # 请求API
            response = requests.put(url=url, data=data, headers=headers)
        response_json = response.json()
        
        if response_json['code'] == 200:
            print("\nUpload success:", filename) # 加个\n防止覆盖上传进度条
            # 是否在上传后删除文件
            if remove_after_upload:
                os.remove(filename)
        else:
            raise Exception("{} Upload failed: {}".format(filename, response_json))

    def upload_alist_form(self, token:str, filename: str):
        '表单上传文件（已废弃）'
        # 文件名处理
        filename_split = os.path.split(filename)
        target_filename = filename_split[1] # 目标文件名
        target_dir = os.path.split(filename_split[0])[1] # 目标文件夹
        filepath = "/quark/{}/{}".format(target_dir, target_filename)
        filepath = quote(filepath) # URL编码

        # 请求参数
        #token = self.get_alist_token()
        url = "http://{}:{}{}".format(host_alist, port_alist, '/api/fs/form')
        headers = {
            "Authorization": token,
            "File-Path": filepath,
            "As-Task": "True",
            "Content-Type": "multipart/form-data",
            "Content-Length": str(os.path.getsize(filename))
        }
        data = File(filename)
        data = urllib3.encode_multipart_formdata()
        # 请求API
        res2 = requests.put(url=url, data=data, headers=headers).json()
        print(res2)

    def set_blrec(self, data: dict):
        '更改blrec设置'
        url = "http://{}:{}{}".format(host_blrec, port_blrec, '/api/v1/settings')
        body = utils.dict2str(data)

        # 请求API
        self.patch(url, data=body)
    
    def get_blrec_data(self, room_id):
        '获取房间信息'
        url = "http://{}:{}{}".format(host_blrec, port_blrec, '/api/v1/tasks/{}/data'.format(room_id))
        response = self.get(url=url)
        response_json = response.json()

        return response_json

## 奇奇怪怪的功能
class utils:
    def dict2str(data: dict):
        '将dict转换为符合http要求的字符串'
        #s = str(data)
        #return s.replace('\'', '\"') 
        return json.dumps(data)# 之前写的什么破玩意
    
    def parse_macro(s: str, data: dict):
        '将配置文件含宏部分解析成对应字符串'
        from functools import reduce
        # 匹配
        re_res = re.findall(r'{[^}]*/[^}]*}', s)
        if not re_res:
            return s
        
        #print(re_res.groups())
        # 解析
        for match_res in re_res:
            split_list = match_res[1:-1].split('/')
            #print(split_list)
            
            if split_list[0] == 'time':
                # 时间解析
                time_now = datetime.datetime.now()
                replaced_s = time_now.strftime(split_list[1])
            else:
                # 字典解析
                replaced_s = str(reduce(lambda x,y:x[y], split_list, data))
            
            # 替换
            s = re.sub(match_res, replaced_s, s)
        
        return s

# functions
## 刷新cookies
def refresh_cookies():
    '刷新cookies'
    import check_cookies
    check_cookies.refresh_cookies(True)

def upload_video(video_filename: str, rec_info=None):
    '上传视频'
    # 文件名处理
    appendices = ['flv', 'jsonl', 'xml', 'jpg', 'mp4'] # 可能存在的后缀名
    filenames = []
    for appendix in appendices:
        # 本地文件名
        local_filename = "{}{}".format(os.path.splitext(video_filename)[0], appendix)
        if not os.path.exists(local_filename):
            continue

        # 远程文件名
        if rec_info:
            dist_dir = utils.parse_macro(remote_dir, rec_info)
            dist_filename = os.path.join(dist_dir, os.path.split(local_filename)[1])

        # [本地文件名, 远程文件名]
        filenames.append([local_filename, dist_filename])
    
    # session
    session = AutoRecSession()

    # 获取token
    token = session.get_alist_token()

    # 上传文件
    pool = multiprocessing.Pool()
    for i in filenames:
        local_filename = i[0]
        dist_filename = i[1]
        pool.apply_async(session.upload_alist_action, args=[token, local_filename, dist_filename])
    pool.close()
    pool.join()

# 加载toml
if not os.path.exists("settings.toml"):
    with open("settings.toml", 'w', encoding='utf-8') as f:
        print("正在导出默认配置")
        DEFAULT_SETTINGS = r"""[blrec]
host_blrec = 'localhost'
port_blrec = 2233

[alist]
port_alist = 5244
host_alist = 'localhost'
username = 'wase'
password = 'AFFA9DBA2C1A74EB34F1585110B0A414F9693AF93BC52C218BE2EEBE7309C43B'
# password format: sha256(<your password>-https://github.com/alist-org/alist)
remote_dir = '/quark/我的备份/来自：TIMI Leave 电脑备份/records/2024_下/{time/%y%m%d}_{room_info/title}'
# usage: {time/<time formatting expressions>} or {<keys of recording properties>/<attribute>}
# (Refer to README.md)

[server]
host_server = 'localhost'
port_server = 23560
"""
        f.write(DEFAULT_SETTINGS)
        quit()
else:
    with open("settings.toml", 'r', encoding='utf-8') as f:
        settings = toml.load(f)

# const
## blrec
settings_blrec = settings['blrec']
host_blrec = settings_blrec['host_blrec']
port_blrec = settings_blrec['port_blrec']

## alist
settings_alist = settings['alist']
host_alist = settings_alist['host_alist']
port_alist = settings_alist['port_alist']
username = settings_alist['username']
password = settings_alist['password']
remote_dir = settings_alist['remote_dir']

## server
settings_server = settings['server']
host_server = settings_server['host_server']
port_server = settings_server['port_server']

# main
if __name__ == "__main__":
    # 输出PID，方便结束进程
    pid = os.getpid()
    with open("pid", 'w') as f:
        f.write(str(pid))
    print("service started: ", pid)

    # 监听
    addr = (host_server, port_server)
    server = HTTPServer(addr, RequestHandler)
    server.serve_forever()
