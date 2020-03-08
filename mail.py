# EMAIL be1myself@foxmail.com
# POP jzzqhzfgmcolcadh
# IMAP bbortygtradwbjbj

import smtplib
import poplib
import imaplib
import email
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

smtp_server_host = 'smtp.qq.com'
smtp_server_port = 465
imap_server_host = 'imap.qq.com'
imap_server_port = 993
sender_name = '发件人'
sender_address = 'be1myself@foxmail.com'
sender_password = 'bbortygtradwbjbj'
receiver_name = '收件人'
receiver_address = '50364830@qq.com'


def send():
    message_subject = '邮件主题'
    message_context = '邮件内容'
    # 邮件对象，用于构建邮件
    message = MIMEText(message_context, 'plain', 'utf-8')
    # 设置发件人（声称的）
    message['From'] = formataddr([sender_name, sender_address])
    # 设置收件人（声称的）
    message['To'] = formataddr([receiver_name, receiver_address])
    # 设置邮件主题
    message['Subject'] = Header(message_subject, 'utf-8')

    # 连接smtp服务器。如果没有使用SSL，将SMTP_SSL()改成SMTP()即可其他都不需要做改动
    email_client = smtplib.SMTP_SSL(smtp_server_host, smtp_server_port)
    try:
        # 验证邮箱及密码是否正确
        email_client.login(sender_address, sender_password)
        print(f'smtp----login success, now will send an email to {receiver_address}')
    except Exception as ex:
        print('smtp----sorry, username or password not correct or another problem occur' + str(ex))
    else:
        # 发送邮件
        email_client.sendmail(sender_address, receiver_address, message.as_string())
        print(f'smtp----send email to {receiver_address} finish')
    finally:
        # 关闭连接
        email_client.close()


def receive():
    try:
        # 连接imap服务器。如果没有使用SSL，将IMAP4_SSL()改成IMAP4()即可其他都不需要做改动
        email_server = imaplib.IMAP4_SSL(host=imap_server_host, port=imap_server_port)
        print('imap4----connect server success, now will check username')
    except Exception as ex:
        print('imap4----sorry the given email server address connect time out' + str(ex))
    try:
        # 验证邮箱及密码是否正确
        email_server.login(sender_address, sender_password)
        print('imap4----username exist, now will check password')
    except:
        print('imap4----sorry the given email address or password seem do not correct')

    # 邮箱中其收到的邮件的数量
    email_server.select()
    email_count = len(email_server.search(None, 'ALL')[1][0].split())
    print(email_count)
    # 通过fetch(index)读取第index封邮件的内容；这里读取最后一封，也即最新收到的那一封邮件
    typ, email_content = email_server.fetch(f'{email_count}'.encode(), '(RFC822)')
    # 将邮件内存由byte转成str
    email_content = email_content[0][1].decode()
    msg = email.message_from_string(email_content)
    for part in msg.walk():
        if not part.is_multipart():
            print(part.get_payload(decode=True).decode('utf-8'))
            # 关闭select
    email_server.close()
    # 关闭连接
    email_server.logout()


receive()
