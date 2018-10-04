# 此脚本用来定期查询东北大学莘莘学子的成绩，发现GPA更新后给自己发送通知邮件
可能需要安装的库有requests,schedule,pytesseract,推荐使用pip安装，在Linux下可以使用如下命令进行安装
```sh
sudo apt-get install python-pip         
sudo pip install requests
sudo pip install schedule
sudo pip install pytesseract
```
账户密码等信息在源码内设置，在GLOBAL变量里，其中发送邮箱账户需要开通pop3服务，然后把授权码写到GLOBAL\['PASS'\]里，具体怎么开通自己搜索吧
对于定时设置，参考以下链接[python用schedule模块实现定时任务](https://blog.csdn.net/zd147896325/article/details/80003982)

