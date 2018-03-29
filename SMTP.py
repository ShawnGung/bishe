#coding=utf-8
import smtplib
from email.mime.text import MIMEText


def send(content):
    msg_from='shawngung@163.com'                                 #发送方邮箱
    passwd='a84615814A'                                   #填入发送方邮箱的授权码
    msg_to='729713735@qq.com'                                  #收件人邮箱
                            
    subject="数据通知"                                     #主题     
    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['From'] = msg_from
    msg['To'] = msg_to
    s = smtplib.SMTP()
    s.connect("smtp.163.com", 25)  # 25 为 SMTP 端口号
    try:    
        s.login(msg_from, passwd)
        s.sendmail(msg_from, msg_to, msg.as_string())
        print ("发送成功")
    except smtplib.SMTPException as e:
        print(e)
        print ("发送失败")
    finally:
        s.quit()

if __name__ == '__main__':
    send('目前有5条数据\
目前有5条数据\
剩下城市:广东省\
遍历情况:(20.617825,24.810879),(110.356639,116.887613)\
剩下设施:银行\
日志情况:')
