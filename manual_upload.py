import autorec
import getopt, os, sys

def usage():
    '--help'
    print("""上传指定目录中的所有文件到指定目录(不支持嵌套目录)
-p <pathname>\t要上传的文件所在目录
-d <dest_dir>\t要上传到的远程文件夹名称
-r\t上传完成后删除原文件(optional)
""")
    quit()

def main():
    # 初始化
    remove_after_upload = False
    local_dir = ""
    dest_dir = ""

    # 解析参数
    options, args = getopt.getopt(sys.argv[1:], "hf:d:", ["help"])
    for name, value in options:
        if name in ("-h","--help"):
            usage()
        elif name == "-d":
            dest_dir = value
        elif name == "-p":
            local_dir = value
        elif name == "-r":
            remove_after_upload = True
    
    # 检查参数
    if local_dir == "" or dest_dir == "":
        print("参数不全")
        usage()
    
    # 获取文件名，去除文件夹
    filenames = os.listdir(local_dir)
    for idx, filename in enumerate(filenames):
        if os.path.isdir(filename):
            del filenames[idx]
    
    # 获取token
    session = autorec.AutoRecSession()
    token = session.get_alist_token()

    # 上传
    total = len(filenames)
    for idx, filename in enumerate(filenames):
        local_filename = os.path.join(local_dir, filename)
        dest_filename = os.path.join(dest_dir, filename)
        print("正在上传：{} -> {} ({}/{})".format(local_filename, dest_filename, idx+1, total))
        session.upload_alist(token, local_filename, dest_dir, remove_after_upload)
    
if __name__ == "__main__":
    main()
