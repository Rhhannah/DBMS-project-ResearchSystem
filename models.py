from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# 1. 院系表 (Department)
class Department(db.Model):
    __tablename__ = 'departments'
    dep_id = db.Column(db.String(20), primary_key=True)
    dep_name = db.Column(db.String(50), nullable=False)
    school_id = db.Column(db.String(20))

    # 可以添加字符串表示，便于调试
    def __repr__(self):
        return f'<Department {self.dep_name}>'


# 2. 教师表 (Teacher)
class Teacher(db.Model):
    __tablename__ = 'teachers'
    teacher_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    sex = db.Column(db.String(10))
    age = db.Column(db.Integer)
    title = db.Column(db.String(50))
    position = db.Column(db.String(50))
    email = db.Column(db.String(100), nullable=False)
    tel = db.Column(db.String(20))

    # 外键和关系
    dep_id = db.Column(db.String(20), db.ForeignKey('departments.dep_id'))
    department = db.relationship('Department', backref='teachers')

    def __repr__(self):
        return f'<Teacher {self.name} ({self.teacher_id})>'


# 3. 任务表 (Task)
class Task(db.Model):
    __tablename__ = 'tasks'
    task_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_name = db.Column(db.String(100), nullable=False)
    format_file = db.Column(db.String(200))
    start_time = db.Column(db.DateTime, default=datetime.now)
    end_time = db.Column(db.DateTime)
    reminder_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='draft')
    #新增字段：用于保存草稿的邮件内容
    email_subject = db.Column(db.String(200))  # 保存自定义标题
    email_content = db.Column(db.Text)  # 保存自定义正文

    def __repr__(self):
        return f'<Task {self.task_name}>'


# 4. 任务-教师关联表
class TaskRecipient(db.Model):
    __tablename__ = 'task_recipient'
    id = db.Column(db.Integer, primary_key=True)

    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'))
    teacher_id = db.Column(db.String(20), db.ForeignKey('teachers.teacher_id'))

    is_replied = db.Column(db.Boolean, default=False)
    sent_time = db.Column(db.DateTime)

    # 关系定义
    teacher = db.relationship('Teacher', backref='task_recipients')
    task = db.relationship('Task', backref='recipients')

    def __repr__(self):
        return f'<TaskRecipient {self.teacher_id} -> {self.task_id}>'


# 5. 回收文件表 (Recycled_Excel) - 改进版
class RecycledExcel(db.Model):
    __tablename__ = 'recycled_excels'
    r_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    file_path = db.Column(db.String(200))
    upload_time = db.Column(db.DateTime, default=datetime.now)

    # 外键
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'))
    teacher_id = db.Column(db.String(20), db.ForeignKey('teachers.teacher_id'))

    # 添加关系定义
    teacher = db.relationship('Teacher', backref='recycled_files')
    task = db.relationship('Task', backref='recycled_files')

    def __repr__(self):
        return f'<RecycledExcel {self.file_path}>'