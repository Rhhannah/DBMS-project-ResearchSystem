import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mailer import MailClient


def test_mail_client():
    # 创建邮件客户端实例
    mail_client = MailClient()

    # 测试数据
    test_data = {
        'to_email': 'test1c2025@163.com',  # 您的测试邮箱
        'subject': '测试邮件 - 科研任务通知',
        'content': '''
        <html>
        <body>
            <h2>尊敬的老师：</h2>
            <p>这是一封<strong>测试邮件</strong>，用于验证邮件发送功能。</p>
            <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px;">
                <p><strong>任务名称：</strong>2024年度科研工作量统计测试</p>
                <p><strong>截止时间：</strong>2024-12-31</p>
                <p><strong>说明：</strong>请及时完成相关材料填写</p>
            </div>
            <p>如有问题，请联系科研管理办公室。</p>
            <hr>
            <p style="color: #666; font-size: 12px;">此邮件为系统自动发送，请勿回复。</p>
        </body>
        </html>
        ''',
        'attachment_path': 'static/uploads\20251130225317_.xlsx'
    }

    print("开始发送测试邮件...")
    print(f"收件人: {test_data['to_email']}")
    print(f"主题: {test_data['subject']}")

    # 发送邮件
    success, message = mail_client.send_task_email(
        test_data['to_email'],
        test_data['subject'],
        test_data['content'],
        test_data['attachment_path']
    )

    # 输出结果
    if success:
        print("✅ 邮件发送成功！")
        print(f"返回信息: {message}")
    else:
        print("❌ 邮件发送失败！")
        print(f"错误信息: {message}")


if __name__ == "__main__":
    test_mail_client()