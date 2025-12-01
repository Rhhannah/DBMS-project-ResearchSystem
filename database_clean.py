import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, Task, TaskRecipient

# 创建Flask应用并配置数据库
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///research_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)


def clear_task_data():
    """清空任务数据"""
    with app.app_context():  # 关键：创建应用上下文
        try:
            # 获取当前数据量
            task_count = Task.query.count()
            recipient_count = TaskRecipient.query.count()

            print("当前数据统计：")
            print(f"  - 任务数量: {task_count}")
            print(f"  - 收件人记录: {recipient_count}")

            if task_count == 0 and recipient_count == 0:
                print("✅ 数据库已经是空的")
                return

            # 执行删除
            print("正在清空数据...")

            # 先删除关联表
            deleted_recipients = TaskRecipient.query.delete()
            print(f"✅ 删除了 {deleted_recipients} 条收件人记录")

            # 再删除主表
            deleted_tasks = Task.query.delete()
            print(f"✅ 删除了 {deleted_tasks} 个任务")

            db.session.commit()
            print("✅ 数据清空完成！")

        except Exception as e:
            db.session.rollback()
            print(f"❌ 清空失败: {str(e)}")


if __name__ == "__main__":
    clear_task_data()