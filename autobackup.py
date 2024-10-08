import autorec

def add_task(url, local_dir, config_file):
    '添加任务'
    import requests, json
    # 请求参数
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "local_dir": local_dir,
        "config_toml": config_file
    }

    # 请求API
    response = requests.post(url=url, data=json.dumps(data), headers=headers)
    data = response.json()
    print("添加成功", data['data'], sep='\n')

def del_task(url, index):
    '删除任务'
    import requests, json
    # 请求参数
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "id": index,
    }

    # 请求API
    response = requests.delete(url=url, data=json.dumps(data), headers=headers)
    data = response.json()
    print("删除提交成功", data['data'], sep='\n')

def show_task(url):
    '列出任务'
    import requests, json
    # 请求参数
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "id": 0,
    }

    # 请求API
    response = requests.get(url=url, data=json.dumps(data), headers=headers)
    data = response.json()
    print(data['data'], sep='\n')

def usage():
    '--help'
    print("""添加定时备份任务
-m/--mode <mode>\t使用模式，a: 新增，s:查询现有任务，d:删除，默认值s
-p/--path <pathname>\t要备份的目录，新增任务必填
-c/--config <config_file>\t备份使用的服务器配置，新增任务必填，默认值settings.toml
-i/--id <id>\t要删除的任务ID，删除任务必填
e.g:
python autobackup.py -m a -c settings.toml -p /home/123
python autobackup.py -m d -i 0
python autobackup.py -m s
""")
    quit()

def main():
    import getopt, os, sys, toml
    # 初始化
    local_dir = ""
    mode = "s"
    config_file = "settings.toml"
    index = ""

    # 解析参数
    options, args = getopt.getopt(sys.argv[1:], "hp:m:c:i:", ["help"])
    for name, value in options:
        if name in ("-h","--help"):
            usage()
        elif name in ("-p","--path"):
            local_dir = value
        elif name in ("-c","--config"):
            config_file = value
        elif name in ("-i","--index"):
            index = int(value)
        elif name in ("-m","--mode"):
            mode = value

    # 检查参数
    if (mode == 'a' and local_dir == "") or (mode == 'd' and index == ""):
        print("参数不全")
        usage()

    # 请求地址    
    with open("settings.toml", 'r', encoding='utf-8') as f:
        settings = toml.load(f)
    url = "http://{}:{}/autobackup".format(
        settings['server']['host_server'], 
        settings['server']['port_server'],
        )

    # 切换模式
    if mode == 's':
        show_task(url)
    elif mode == 'a':
        add_task(url, config_file=config_file, local_dir=local_dir)
    elif mode == 'd':
        del_task(url, index)

if __name__ == "__main__":
    main()
