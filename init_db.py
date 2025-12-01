from app import app
from models import db, Department, Teacher
import random


def create_fake_data():
    with app.app_context():
        # 1. 重置数据库
        db.drop_all()
        db.create_all()

        # 2. 生成院系
        # 1. 创建院系
        deps = [
            Department(dep_id="D01", dep_name="计算机系", school_id="S01"),
            Department(dep_id="D02", dep_name="软件工程系", school_id="S01"),
            Department(dep_id="D03", dep_name="信息安全系", school_id="S01")
        ]
        # 插入院系数据
        db.session.add_all(deps)
        db.session.commit()  # 提交事务

        # 2. 手动添加教师信息（包括教师ID、姓名、性别、年龄、职称、邮箱、电话等）
        teachers_data = [
            {"teacher_id": "T202501", "name": "赵伟", "sex": "男", "age": 35, "title": "教授", "position": "系主任",
             "email": "test1c2025@163.com", "tel": "138000001", "dep_id": "D01"},  # 指定 dep_id
            {"teacher_id": "T202502", "name": "钱娜", "sex": "女", "age": 40, "title": "副教授", "position": "党委书记",
             "email": "test2c2025@163.com", "tel": "138000002", "dep_id": "D02"},  # 指定 dep_id
            {"teacher_id": "T202503", "name": "孙敏", "sex": "女", "age": 32, "title": "讲师", "position": "无",
             "email": "DBMS_T1@163.com", "tel": "138000003", "dep_id": "D03"},  # 指定 dep_id
            {"teacher_id": "T202504", "name": "李静", "sex": "男", "age": 38, "title": "教授", "position": "系主任",
             "email": "DBMS_T2@163.com", "tel": "138000004", "dep_id": "D01"},  # 指定 dep_id
            {"teacher_id": "T202505", "name": "周强", "sex": "男", "age": 45, "title": "副教授", "position": "党委书记",
             "email": "DBMS_T3@163.com", "tel": "138000005", "dep_id": "D02"}  # 指定 dep_id
        ]

        # 生成教师对象并添加到列表
        teachers = []
        for data in teachers_data:
            dep = Department.query.filter_by(dep_id=data["dep_id"]).first()  # 查询对应的院系实例
            if dep:  # 确保院系存在
                teacher = Teacher(
                    teacher_id=data["teacher_id"],
                    name=data["name"],
                    sex=data["sex"],
                    age=data["age"],
                    title=data["title"],
                    position=data["position"],
                    email=data["email"],
                    tel=data["tel"],
                    dep_id=dep.dep_id  # 将对应院系的 dep_id 插入教师记录中
                )
                teachers.append(teacher)

        # 将教师数据添加到数据库
        db.session.add_all(teachers)
        db.session.commit()  # 提交事务


if __name__ == '__main__':
    create_fake_data()