import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from email.utils import formataddr  # 仍然从 utils 导入
from email.header import decode_header  # 从 header 导入 decode_header

class MailClient:
    def __init__(self):
        # 配置邮件服务器信息
        self.smtp_server = "smtp.163.com"  # 163 邮箱的 SMTP 服务器地址
        self.smtp_port = 465  # SSL 端口，163邮箱的SMTP端口为 465
        self.sender_email = "18672133895@163.com"  # <-- 需要填写你自己的163邮箱地址
        self.password = "YXtFC34MKwXkQB4Y"  # <-- 需要填写你从163邮箱获取的授权码

    def send_task_email(self, to_email, subject, content, attachment_path=None):
        """
        发送带有 Excel 附件的任务邮件
        """
        try:
            # 1. 构建邮件对象
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject

            # 2. 添加正文
            msg.attach(MIMEText(content, 'html', 'utf-8'))

            # 3. 添加附件 (Excel模板)
            if attachment_path and os.path.exists(attachment_path):
                filename = os.path.basename(attachment_path)
                with open(attachment_path, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=filename)
                # 添加头信息，设置下载文件名
                part['Content-Disposition'] = f'attachment; filename="{filename}"'
                msg.attach(part)

            # 4. 连接服务器发送邮件
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            server.login(self.sender_email, self.password)
            server.send_message(msg)
            server.quit()

            return True, "发送成功"
        except Exception as e:
            return False, str(e)

