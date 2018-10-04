#-*-encoding:utf8-*-
#!/usr/bin/env python

import re
import sys
import time
import smtplib
import schedule
import requests
import pytesseract
from PIL import Image
from smtplib import SMTP_SSL
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#定义全局变量，请在这里进行账户设置
GLOBAL = {'STU_ID': '',         #学号
          'STU_PASS': '',       #密码
          'SEND_ACCOUNT': '',   #发送邮箱账号
          'SEND_PASS': '',      #发送邮箱授权码
          'RECV_ACCOUNT': ''}   #接收邮箱账号

##########发送邮件函数###############
def send_email(title, message):
    #qq邮箱服务器地址
    mail_server= 'smtp.qq.com'

    #构造邮件对象
    msg = MIMEMultipart('mixed')
    msg['Subject'] = title
    msg['From'] = GLOBAL['SEND_ACCOUNT']
    msg['To'] = GLOBAL['RECV_ACCOUNT']
    msg.attach(MIMEText(message, 'html', 'gbk'))

    #ssl登录
    smtp = SMTP_SSL(mail_server)
    smtp.login(GLOBAL['SEND_ACCOUNT'], GLOBAL['SEND_PASS'])

    #发送成绩
    smtp.sendmail(GLOBAL['SEND_ACCOUNT'], GLOBAL['RECV_ACCOUNT'], msg.as_string())
    smtp.quit()

############识别验证码中的运算式###############
def identify_code(img_path):
    img = Image.open(img_path)

    #转为灰度图
    img = img.convert('L')

    #进行二值化
    binaryImage = img.point(initTable(), '1')

    #获取验证码
    verify_code = pytesseract.image_to_string(binaryImage)

    #对识别结果进行验证
    validate_str = '1234567890+*='
    if verify_code is None or len(verify_code) < 4:
        return None
    for i in range(len(verify_code)):
        if verify_code[i] not in validate_str:
            return None
    return verify_code

############二值化函数，参数为阈值###############
def initTable(threshold = 140):
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)
    return table

###########进行登录，获取成绩###################
def get_gpa(stu_ID, stu_pwd):
    #初始化登录页面网址，验证码值
    url = 'https://zhjw.neu.edu.cn/ACTIONLOGON.APPPROCESS?mode=1&applicant=ACTIONQUERYSTUDENTSCORE'
    Agnomen = 0

    #进行登录,当验证码一直识别不出来时一直循环
    while Agnomen == 0:
        logon_page = requests.get(url)

        #获取页面的cookie值
        cookies = logon_page.cookies.get_dict()

        #获取验证码图片的uri
        verify_pic_url = re.search(r'id="Agnomen"\s*style="(.*?)"\s*/>\s*<img\s*src="(.*?)"', logon_page.text)

        #未找到uri的时候,进行再次请求
        if verify_pic_url is None:
            continue

        #获取验证码图片，写入文件
        verify_pic = requests.get('https://zhjw.neu.edu.cn' + '/' + verify_pic_url.groups()[1], cookies=cookies)
        with open('code.jpg', 'wb') as fp:
            fp.write(verify_pic.content)

        #进行验证码的识别
        verify_code = identify_code('code.jpg')

        #验证码识别失败的情况
        if verify_code is None:
            Agnomen = 0
            continue

        #识别成功的话进行运算
        if verify_code[1] == '+':
            Agnomen = int(verify_code[0]) + int(verify_code[2])
        elif verify_code[1] == '*':
            Agnomen = int(verify_code[0]) * int(verify_code[2])
        else:
            Agnomen = 0

    #进行成绩查询,构造post数据
    data = {'WebUserNO':stu_ID, 
            'applicant':'ACTIONQUERYSTUDENTSCORE', 
            'Password':stu_pwd, 
            'Agnomen':str(Agnomen), 
            'submit7':'%B5%C7%C2%BC'}

    #查询
    query_page = requests.post('https://zhjw.neu.edu.cn/ACTIONLOGON.APPPROCESS?mode=', data=data, cookies=cookies)

    #搜索绩点
    search_result = re.search(ur'平均学分绩点：(.*?)\s*</td>', query_page.text) 
    if search_result is None:
        print '没有找到绩点'
        sys.exit() 

    #获取绩点值
    gpa = search_result.groups()[0]

    return [query_page.text, gpa]

##########判断GPA是否更新以及更新以后的操作################
def gpa_has_updated():
    #查询最新成绩
    new_data = get_gpa(GLOBAL['STU_ID'], GLOBAL['STU_PASS'])

    #如果发生变化
    if GLOBAL['gpa'] != new_data[1]:
        print "您的GPA发生了异动"
        send_email('您的GPA发生了异动', GLOBAL['page'] + new_data[0])
        GLOBAL['gpa'] = new_data[1]
        GLOBAL['page'] = new_data[0]

###########主函数#####################################
if __name__ == '__main__':
    #进行首次成绩查询并测试
    result = get_gpa(GLOBAL['STU_ID'], GLOBAL['STU_PASS'])

    #进行人工确认
    q1 = 'Your GPA is:' + result[1] + '  Right(Y/N)?'
    choice = raw_input(q1)
    if not (choice == 'Y' or choice == 'y'):
        print 'Please set your account in the code properly'
        sys.exit()

    #进行邮件测试
    send_email('首次邮件测试', '')
    q2 = 'Have you received a test email(Y/N)?'
    choice = raw_input(q2)
    if not (choice == 'Y' or choice == 'y'):
        print 'Please check your email setting int the code!'
        sys.exit()

    #测试完毕，开始定期执行
    print 'Test OK! Let\'s go go go !'
    GLOBAL['gpa'] = result[1]
    GLOBAL['page'] = result[0]

    #设置定期执行时间
    schedule.every(5).seconds.do(gpa_has_updated)
    
    #每天10.30发一封邮件给自己确保程序没挂
    schedule.every().day.at("10:30").do(send_email, '这是一封测试邮件,确保您的程序还活着', '')

    while True:
        schedule.run_pending()
