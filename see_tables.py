import pandas as pd
import sqlite3

# 连接到数据库
conn = sqlite3.connect('./instance/research_system.db')

# 创建游标
cursor = conn.cursor()


# 读取表到 DataFrame
teachers_df = pd.read_sql('SELECT * FROM teachers', conn)
departments_df = pd.read_sql('SELECT * FROM departments', conn)
tasks_df = pd.read_sql('SELECT * FROM tasks', conn)
task_recipient_df = pd.read_sql('SELECT * FROM task_recipient', conn)

# print("teachers表:")
# print(teachers_df.head())
#
# print("departments表:")
# print(departments_df.head())

print("tasks表:")
print(tasks_df[['task_id','end_time','status']])
#
# print("task_recipient表:")
# print(task_recipient_df.head())