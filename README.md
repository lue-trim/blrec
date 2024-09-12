# autorec
一个利用blrec/录播姬的webhook和alist的API实现录播完成后自动把文件上传到服务器并删除本地文件、自动更新cookies操作的server
理论上稍微改改，也能用在命令行版录播姬上

# 基于项目
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
## 上传路径模板 
原理：在视频后处理完成后会自动获取一次录制信息，并填充到`[alist]/remote_dir`所设定的路径模板中

模板示例：`{room_info/room_id}_{user_info/name}/{time/%y%m%d}_{room_info/title}`

自动填充模板格式详情：\
`time`开头: 上传前立即获取的时间信息，`/`后接python的时间格式化字符串 
`room_info`/`user_info`/`task_status`开头: 从blrec处获取的录制信息，`/`后接具体的属性名称

举例: 从blrec获取的录制信息如下: \
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
# 运行
直接在终端运行`python autorec.py`，或者自己写一个`autorec.service`添加到systemctl都可以，能跑起来就行
