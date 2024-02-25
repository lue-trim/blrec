# autorec
一个利用blrec/录播姬的webhook和alist的API实现录播完成后自动把文件上传到服务器并删除本地文件、自动更新cookies操作的server
理论上稍微改改，也能用在命令行版录播姬上

# 基于项目
- [acgnhiki / blrec](https://github.com/acgnhiki/blrec)；
- [SocialSisterYi / bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect)；
- [alist-org / docs](https://github.com/alist-org/docs)

# 要求
## 环境
环境要求写在`requirements.txt`里
`pip install -r requirements.txt`
实际上版本号不一定需要按文件里的这么高，低一点也能运行
## Python版本
在Python3.11下测试，但是一般只要是Python3都能跑起来

# 配置
## 配置文件
- 第一次运行的时候会生成示例`settings.toml`，需要根据实际运行环境自行修改参数
- 在`settings.toml`中设置blrec的主机与端口号
- 在`settings.toml`中设置alist的主机、端口号、用户名、加密后的密码（获取方法[在这](https://alist-v3.apifox.cn/api-128101242)）
## blrec设置
1. 在blrec的Webhook设置中添加autorec的url(默认是`http://localhost:23560`)
2. 至少勾选`VideoPostprocessingCompletedEvent`（自动上传视频和弹幕）和`RecordingFinishedEvent`（自动更新cookies）
## 自动更新cookies功能
1. 要使用此功能需要使用另一个项目[bili_login](https://github.com/lue-trim/bilibiliLogin)来扫码获取`cookies.txt`和`data.json`
2. 把上述两个文件`cookies.txt`和`data.json`放到本仓库目录下
3. 每次blrec发送`RecordingFinishedEvent`事件时会自动读取、更新并设置cookies
# 修改并运行
1. 要上传的本地文件路径和上传到服务器的目标路径写死在autorec.py的upload_video方法里，有需要自己改
2. `python autorec.py`或者把`autorec.service`添加到systemctl（`autorec_service.sh`需要自己根据实际环境改一下）
