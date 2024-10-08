# autorec
一个利用blrec的webhook和alist的API，实现录播完成后自动把文件上传到服务器并删除本地文件、每日自动备份文件到其他存储、自动更新cookies操作的脚本  
理论上稍微改改API，也能用在命令行版录播姬上
## 基于项目
- [acgnhiki/blrec](https://github.com/acgnhiki/blrec)；
- [SocialSisterYi/bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect)；
- [alist-org/docs](https://github.com/alist-org/docs)

# 要求
## 环境
环境要求写在`requirements.txt`里  
`pip install -r requirements.txt`  
实际上版本号不一定需要按文件里的这么高，低一点也能运行
## Python版本
在Python3.11下测试，但是一般只要是Python3都能跑起来

# 配置说明
## 初次设置
第一次运行的时候会生成配置模板`settings.toml`，需要根据实际运行环境自行修改参数

## 录制完成后立即自动上传
原理：在视频后处理完成后会自动获取一次录制信息，并填充到`[alist]/remote_dir`所设定的路径模板中  
该流程不可跳过，如果只设置每日自动备份，不设置立即上传的部分，是会报错的……
### 使用配置
#### blrec
1. 在blrec的Webhook设置中添加autorec的url(默认是`http://localhost:23560`)
1. 至少勾选`VideoPostprocessingCompletedEvent`（自动上传视频和弹幕）和`RecordingFinishedEvent`（自动更新cookies）
1. 在`settings.toml`\[blrec\]模块中设置blrec的主机与端口号
#### autorec
- 需在`settings.toml`\[alist\]模块中设置alist的主机、端口号、用户名、加密后的密码（获取方法[在这](https://alist-v3.apifox.cn/api-128101242)）
- 各项参数的具体用法可以参考第一次运行时生成的配置模板
- **注意**：如果要设置每日自动备份，记得把`remove_after_upload`给设成`false`
##### 上传路径模板说明 
模板示例：`{room_info/room_id}_{user_info/name}/{time/%y%m%d}_{room_info/title}`

自动填充模板格式详情：  
- `time`开头:  
上传前立即获取的时间信息，`/`后接python的时间格式化字符串  
- `room_info`/`user_info`/`task_status`开头:  
从blrec处获取的录制信息，`/`后接具体的属性名称

举例: 从blrec获取的录制信息如下:   
（可以通过向blrec的`/api/v1/tasks/{room_id}/data`发送get请求获取）
```json
{
  "user_info": { 
    "name": "早稻叽", 
    "gender": "女", 
    "face": "https://i1.hdslb.com/bfs/face/***.jpg", 
    "uid": 1950658, 
    "level": 6, 
    "sign": "<ChaosLive>励志给人类带来幸福的光之恶魔✨商务合作请戳1767160966（不看私信，谢）" 
  },
  "room_info": {
    "uid": 1950658,
    "room_id": 41682,
    "short_room_id": 631,
    "area_id": 745,
    "area_name": "虚拟Gamer",
    "parent_area_id": 9,
    "parent_area_name": "虚拟主播",
    "live_status": 2,
    "live_start_time": 0,
    "online": 0,
    "title": "晚上不好",
    "cover": "https://i0.hdslb.com/bfs/live/new_room_cover/***.jpg",
    "tags": "VTUBER,VUP,虚拟主播,歌姬,早稻叽,虚拟UP主",
    "description": "诞生于粉丝满满心意的全新3D虚拟星球正在开幕中！5位重磅UP首批强势入驻！@泠鸢yousa@兰音reine@C酱です@AIChannel中国绊爱@早稻叽（排名不分先后）\n锁定直播间，来和心爱的主播贴贴、坐摩天轮吧~观看直播，还有机会赢取苹果14手机、100元现金红包哟~观看有礼一键传送https://www.bilibili.com/blackboard/live/activity-eWPyQBs0W6.html"
  },
  "task_status": {
    "monitor_enabled": true,
    "recorder_enabled": true,
    "running_status": "waiting",
    "stream_url": "https://d1--ov-gotcha05.bilivideo.com/***",
    "stream_host": "d1--ov-gotcha05.bilivideo.com",
    "dl_total": 5632504232,
    "dl_rate": 475005.92442482925,
    "rec_elapsed": 10838.652142584091,
    "rec_total": 5627981824,
    "rec_rate": 474669.98430827376,
    "danmu_total": 0,
    "danmu_rate": 0,
    "real_stream_format": null,
    "real_quality_number": null,
    "recording_path": "",
    "postprocessor_status": "waiting",
    "postprocessing_path": null,
    "postprocessing_progress": null
  }
}
```
## 下播后自动更新cookies
要使用此功能需要使用另一个项目[bili_login](https://github.com/lue-trim/bilibiliLogin)来扫码获取`cookies.txt`和`data.json`  
1. 把上述两个文件`cookies.txt`和`data.json`放到本仓库目录下
1. 每次blrec发送`RecordingFinishedEvent`事件时会自动读取、更新并设置cookies  

要关闭该功能，只需在blrec的设置里关掉对应的webhook就行

## 每日自动备份
可以在每天指定时段向特定alist存储备份刚刚录制好的文件（但是不能使用立即上传功能的路径模板）  
要关闭该功能，把`autobackup.servers`置空就可以
### 使用配置
- 在`settings.toml`\[autobackup\]模块中的`interval`项设置时间检查间隔（区间越短CPU占用越大）
- 按照与\[alist\]模块相同的格式，把要添加到的存储添加到`autobackup.servers`列表，可以同时备份到多个存储  
（参见第一次运行时生成的配置模板）  
（除了不能用路径模板以外，其他内容都和\[alist\]里一样）  
- 对于每个`autobackup.servers`项，都需要设置一个预定上传时间  
（格式是`"%H:%M:%S"`）
- **注意**：如果要备份到多个存储，并且需要上传后自动删除文件，记得把`remove_after_upload=true`放在最后一个存储下

## 手动补录/取消备份
运行`python autobackup.py`，通过读取配置文件里的\[autobackup\]设置，增、删、查目前存在的备份任务  
具体使用说明可以加`-h`/`--help`查看

例：
手动加载配置文件并添加备份任务：`python autobackup.py -m a -p /local/records -c upload_config.toml`  
看看现在有哪些任务要备份：`python autobackup.py -m s` 
删掉最早的自动备份任务：`python autobackup.py -m d -i 0`  

## 立即手动上传
运行`python manual_upload.py`，通过读取配置文件里的\[autobackup\]设置（是的，这里没打错），立即上传任意文件夹中的所有文件到指定alist存储  
具体使用说明可以加`-h`/`--help`查看

例：  
立即手动上传：`python manual_upload.py -p /local/records -c upload_config.toml`

# 运行
## 服务端
直接在终端运行`python autorec.py`，或者自己写一个`autorec.service`添加到systemctl都可以，能跑起来就行
## 客户端
主要指的是`python autobackup.py`与`python manual_upload.py`，具体使用帮助可加`-h`/`--help`查看
