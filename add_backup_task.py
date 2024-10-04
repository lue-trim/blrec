import autorec

def usage():
    '--help'
    print("""添加定时备份任务
-p <pathname>\t要备份的目录
""")
    quit()

def main():
    import getopt, os, sys, requests, json
    # 初始化
    local_dir = ""

    # 解析参数
    options, args = getopt.getopt(sys.argv[1:], "hp:", ["help"])
    for name, value in options:
        if name in ("-h","--help"):
            usage()
        elif name == "-p":
            local_dir = value
    
    # 检查参数
    if local_dir == "":
        print("参数不全")
        usage()
    
    # 请求参数
    url = "http://{}:{}".format(
        autorec.settings_server['host_server'], 
        autorec.settings_server['port_server'],
        )
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "local_dir": local_dir,
    }

    # 请求API
    response = requests.put(url=url, data=json.dumps(data), headers=headers)
    data = response.json()
    print(data)
    
if __name__ == "__main__":
    main()
