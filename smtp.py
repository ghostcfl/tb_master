import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from settings import my_sender, my_pass
from logger import get_logger

logger = get_logger()

my_sender = my_sender  # 发件人邮箱账号
my_pass = my_pass  # 发件人邮箱密码
my_user = [
    '946930866@qq.com'
]  # 收件人邮箱账号


def mail(title, content, *args):
    try:
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['From'] = Header(my_sender)  # 发送者
        msg['To'] = Header(",".join(*args))
        # msg['From'] = formataddr(["caifuliang", my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        # msg['To'] = formataddr(["caifuliang", my_user])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject'] = title  # 邮件的主题，也可以说是标题

        server = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 发件人邮箱中的SMTP服务器，端口是25
        server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(my_sender, *args, msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
        logger.info("邮件发送成功")
    except Exception as e:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
        logger.info(e)
        logger.info("邮件发送失败")


def mail_pic(*args):
    msg = MIMEMultipart()
    msg['From'] = Header(my_sender)  # 发送者
    msg['To'] = Header(",".join(*args))
    msg['Subject'] = "登陆二维码"  # 邮件的主题，也可以说是标题
    boby = """
        <br><img src="cid:image1"></br> 
    """
    mail_body = MIMEText(boby, _subtype='html', _charset='utf-8')
    msg.attach(mail_body)
    fp = open("./qrcode.png", 'rb')
    images = MIMEImage(fp.read())
    fp.close()
    images.add_header('Content-ID', '<image1>')
    msg.attach(images)
    # 构造附件1，传送当前目录下的 test.txt 文件
    # att1 = MIMEText(open('qrcode.png', 'rb').read(), 'base64', 'utf-8')
    # att1["Content-Type"] = 'application/octet-stream'
    # # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
    # att1["Content-Disposition"] = 'attachment; filename="登陆二维码.png"'
    # msg.attach(att1)
    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(my_sender, my_pass)
        server.sendmail(my_sender, *args, msg.as_string())
        server.quit()
        # smtpObj.sendmail(my_sender, *args, message.as_string())
        logger.info("邮件发送成功")
    except smtplib.SMTPException as e:
        logger.info("Error: 无法发送邮件")
        return False
    else:
        return True


def mail_reports(title, content, date, *args):
    try:
        msg = MIMEMultipart()
        msg['From'] = Header(my_sender)  # 发送者
        msg['To'] = Header(",".join(args))
        # msg['From'] = formataddr(["caifuliang", my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        # msg['To'] = formataddr(["caifuliang", my_user])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject'] = title  # 邮件的主题，也可以说是标题

        mail_body = MIMEText(content, _subtype='html', _charset='utf-8')
        msg.attach(mail_body)
        # 构造附件1，传送当前目录下的 test.txt 文件
        att1 = MIMEText(open('./reports/reports' + date + '.csv', 'rb').read(), 'base64', 'utf-8')
        att1["Content-Type"] = 'application/octet-stream'
        # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
        att1["Content-Disposition"] = 'attachment; filename="reports.csv"'
        msg.attach(att1)

        server = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 发件人邮箱中的SMTP服务器，端口是25
        server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(my_sender, args, msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
        logger.info("邮件发送成功")
    except Exception as e:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
        logger.info(e)
        logger.info("邮件发送失败")


if __name__ == '__main__':
    mail_pic(["946930866@qq.com"])
