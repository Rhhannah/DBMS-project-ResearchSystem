from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, session
from models import db, Department, Teacher, Task, TaskRecipient, RecycledExcel
from mailer import MailClient  # 导入邮件客户端
from datetime import datetime, timedelta
import os
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///research_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 文件上传配置
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

db.init_app(app)
mail_client = MailClient()  # 创建邮件客户端实例


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# 主页 - 数据概览
@app.route('/')
def dashboard():
    # 统计信息
    total_teachers = Teacher.query.count()
    total_departments = Department.query.count()
    total_tasks = Task.query.count()
    active_tasks = Task.query.filter(Task.status.in_(['active', 'ongoing'])).count()

    # 最近任务
    recent_tasks = Task.query.order_by(Task.start_time.desc()).limit(5).all()

    # 任务状态统计
    task_stats = {
        'draft': Task.query.filter_by(status='draft').count(),
        'active': Task.query.filter_by(status='active').count(),
        'completed': Task.query.filter_by(status='completed').count()
    }

    return render_template('dashboard.html',
                           total_teachers=total_teachers,
                           total_departments=total_departments,
                           total_tasks=total_tasks,
                           active_tasks=active_tasks,
                           recent_tasks=recent_tasks,
                           task_stats=task_stats)


# 联系人管理
@app.route('/contacts')
def contacts():
    departments = Department.query.all()
    selected_dep = request.args.get('department')
    search_query = request.args.get('search', '').strip()

    # 构建查询
    query = Teacher.query

    # 院系筛选
    if selected_dep:
        query = query.filter_by(dep_id=selected_dep)

    # 搜索功能
    if search_query:
        query = query.filter(
            (Teacher.teacher_id.contains(search_query)) |
            (Teacher.name.contains(search_query)) |
            (Teacher.email.contains(search_query))
        )

    teachers = query.all()

    return render_template('contacts.html',
                           teachers=teachers,
                           departments=departments,
                           selected_dep=selected_dep,
                           search_query=search_query)


# 添加教师
@app.route('/add_teacher', methods=['POST'])
def add_teacher():
    try:
        teacher = Teacher(
            teacher_id=request.form['teacher_id'],
            name=request.form['name'],
            sex=request.form['sex'],
            age=int(request.form['age']),
            title=request.form['title'],
            position=request.form['position'],
            email=request.form['email'],
            tel=request.form['tel'],
            dep_id=request.form['dep_id']
        )
        db.session.add(teacher)
        db.session.commit()
        flash('教师添加成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'添加失败: {str(e)}', 'error')

    return redirect(url_for('contacts'))


# 批量导入教师
@app.route('/batch_import_teachers', methods=['POST'])
def batch_import_teachers():
    try:
        print("=== 开始批量导入教师 ===")

        if 'excel_file' not in request.files:
            flash('请选择Excel文件', 'error')
            return redirect(url_for('contacts'))

        file = request.files['excel_file']
        print(f"接收到的文件: {file.filename}")

        if file.filename == '':
            flash('请选择Excel文件', 'error')
            return redirect(url_for('contacts'))

        if file and allowed_file(file.filename):
            # 保存文件
            filename = secure_filename(f"import_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            print(f"文件已保存到: {file_path}")

            # 读取Excel文件
            df = pd.read_excel(file_path)
            print(f"Excel文件读取成功，共 {len(df)} 行数据")
            print("列名:", df.columns.tolist())
            print("前几行数据:")
            print(df.head())

            # 检查必要的列
            required_columns = ['teacher_id', 'name', 'email', 'dep_name']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                error_msg = f'Excel文件缺少必要的列: {", ".join(missing_columns)}'
                print(f"错误: {error_msg}")
                flash(error_msg, 'error')
                return redirect(url_for('contacts'))

            # 获取所有院系映射（名称 -> ID）
            departments = Department.query.all()
            dep_name_to_id = {dep.dep_name: dep.dep_id for dep in departments}

            success_count = 0
            error_count = 0
            error_messages = []

            # 处理每一行数据
            for index, row in df.iterrows():
                try:
                    teacher_id = str(row['teacher_id'])
                    dep_name = str(row['dep_name'])

                    print(f"处理第{index + 2}行: 工号={teacher_id}, 院系={dep_name}")

                    # 检查教师是否已存在
                    existing_teacher = Teacher.query.get(teacher_id)
                    if existing_teacher:
                        error_msg = f"第{index + 2}行: 工号 {teacher_id} 已存在"
                        print(f"错误: {error_msg}")
                        error_count += 1
                        error_messages.append(error_msg)
                        continue

                    # 检查院系名称是否存在
                    if dep_name not in dep_name_to_id:
                        error_msg = f"第{index + 2}行: 院系 '{dep_name}' 不存在。可用院系: {', '.join(dep_name_to_id.keys())}"
                        print(f"错误: {error_msg}")
                        error_count += 1
                        error_messages.append(error_msg)
                        continue

                    # 创建新教师
                    teacher = Teacher(
                        teacher_id=teacher_id,
                        name=str(row['name']),
                        sex=str(row.get('sex', '男')),
                        age=int(row.get('age', 30)) if pd.notna(row.get('age')) else 30,
                        title=str(row.get('title', '')),
                        position=str(row.get('position', '')),
                        email=str(row['email']),
                        tel=str(row.get('tel', '')),
                        dep_id=dep_name_to_id[dep_name]
                    )

                    db.session.add(teacher)
                    success_count += 1
                    print(f"成功添加教师: {teacher_id}")

                except Exception as e:
                    error_msg = f"第{index + 2}行: {str(e)}"
                    print(f"异常错误: {error_msg}")
                    error_count += 1
                    error_messages.append(error_msg)
                    continue

            db.session.commit()
            print(f"导入完成: 成功 {success_count} 条, 失败 {error_count} 条")

            # 显示导入结果
            if success_count > 0:
                flash(f'成功导入 {success_count} 名教师', 'success')
            if error_count > 0:
                flash(f'导入失败 {error_count} 条记录', 'warning')
                for msg in error_messages[:5]:  # 只显示前5条错误
                    flash(msg, 'error')

            # 删除临时文件
            os.remove(file_path)

        else:
            flash('请上传有效的Excel文件 (.xlsx 或 .xls)', 'error')

    except Exception as e:
        print(f"导入过程发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        flash(f'导入失败: {str(e)}', 'error')

    return redirect(url_for('contacts'))


# 下载导入模板
@app.route('/download_import_template')
def download_import_template():
    # 创建示例数据
    sample_data = {
        'teacher_id': ['T202501', 'T202502', 'T202503'],
        'name': ['张三', '李四', '王五'],
        'sex': ['男', '女', '男'],
        'age': [35, 28, 42],
        'title': ['教授', '副教授', '讲师'],
        'position': ['院长', '系主任', '教师'],
        'email': ['zhangsan@example.com', 'lisi@example.com', 'wangwu@example.com'],
        'tel': ['13800138001', '13800138002', '13800138003'],
        'dep_name': ['计算机系', '软件工程系', '信息安全系']
    }

    df = pd.DataFrame(sample_data)

    # 保存到临时文件
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], 'teacher_import_template.xlsx')
    df.to_excel(template_path, index=False, sheet_name='教师数据')

    return send_file(template_path,
                     as_attachment=True,
                     download_name='教师批量导入模板.xlsx')



# 编辑教师
@app.route('/edit_teacher/<teacher_id>', methods=['POST'])
def edit_teacher(teacher_id):
    try:
        teacher = Teacher.query.get_or_404(teacher_id)
        teacher.name = request.form['name']
        teacher.sex = request.form['sex']
        teacher.age = int(request.form['age'])
        teacher.title = request.form['title']
        teacher.position = request.form['position']
        teacher.email = request.form['email']
        teacher.tel = request.form['tel']
        teacher.dep_id = request.form['dep_id']

        db.session.commit()
        flash('教师信息更新成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'更新失败: {str(e)}', 'error')

    return redirect(url_for('contacts'))


# 删除教师
@app.route('/delete_teacher/<teacher_id>')
def delete_teacher(teacher_id):
    try:
        teacher = Teacher.query.get_or_404(teacher_id)

        # 先删除关联数据
        TaskRecipient.query.filter_by(teacher_id=teacher_id).delete()
        RecycledExcel.query.filter_by(teacher_id=teacher_id).delete()

        # 再删除教师
        db.session.delete(teacher)
        db.session.commit()

        flash('教师删除成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'error')

    return redirect(url_for('contacts'))


# 批量删除教师
@app.route('/batch_delete_teachers', methods=['POST'])
def batch_delete_teachers():
    try:
        teacher_ids = request.form.getlist('teacher_ids')
        if not teacher_ids:
            flash('请选择要删除的教师', 'error')
            return redirect(url_for('contacts'))

        # 验证教师ID是否存在
        existing_teachers = Teacher.query.filter(Teacher.teacher_id.in_(teacher_ids)).all()
        existing_ids = [t.teacher_id for t in existing_teachers]

        # 先删除关联数据（使用 synchronize_session=False 避免会话同步问题）
        TaskRecipient.query.filter(TaskRecipient.teacher_id.in_(existing_ids)).delete(synchronize_session=False)
        RecycledExcel.query.filter(RecycledExcel.teacher_id.in_(existing_ids)).delete(synchronize_session=False)

        # 批量删除教师
        delete_count = Teacher.query.filter(Teacher.teacher_id.in_(existing_ids)).delete(synchronize_session=False)
        db.session.commit()

        flash(f'成功删除 {delete_count} 名教师', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'批量删除失败: {str(e)}', 'error')

    return redirect(url_for('contacts'))


# app.py 中修改 task_center 函数
@app.route('/task_center')
def task_center():
    # 1. 获取草稿 (Drafts)
    drafts = Task.query.filter_by(status='draft').order_by(Task.start_time.desc()).all()

    # 2. 获取已发送/历史任务 (History) - 排除草稿
    history_tasks = Task.query.filter(Task.status != 'draft').order_by(Task.start_time.desc()).all()

    teachers = Teacher.query.all()
    departments = Department.query.all()

    return render_template('task_center.html',
                           drafts=drafts,  # 传草稿
                           tasks=history_tasks,  # 传历史任务
                           teachers=teachers,
                           departments=departments)


# 新增：继续编辑草稿的路由
@app.route('/continue_draft/<int:task_id>')
def continue_draft(task_id):
    # 1. 从数据库获取这个草稿任务
    task = Task.query.get_or_404(task_id)
    # 2. 准备下拉框数据
    teachers = Teacher.query.all()
    departments = Department.query.all()
    # 3. 构造 email_template 对象传给前端
    # 这样前端的 value="{{ email_template.subject }}" 就能读到数据了
    email_template = {
        'subject': task.email_subject,
        'content': task.email_content
    }
    # 4. 渲染 task_center.html，并告诉它 "draft_task" 是谁
    return render_template('task_center.html',
                           draft_task=task,  # 核心：传入当前草稿
                           email_template=email_template,  # 传入保存的文字
                           drafts=[], tasks=[],  # 编辑模式下不需要显示列表
                           teachers=teachers,
                           departments=departments)


# 发送任务通知
@app.route('/send_task/<int:task_id>')
def send_task_emails(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        task.status = 'active'

        # 发送邮件通知
        recipients = TaskRecipient.query.filter_by(task_id=task_id).all()
        success_count = 0
        fail_count = 0

        for recipient in recipients:
            teacher = recipient.teacher
            attachment_path = os.path.join(app.config['UPLOAD_FOLDER'], task.format_file) if task.format_file else None

            # 获取自定义邮件主题和正文（如果存在）
            session_key = f'task_email_{task_id}'
            email_template = session.get(session_key, {})

            # 使用自定义主题或默认主题
            if email_template.get('subject'):
                subject = email_template['subject']
            else:
                subject = f"科研任务通知: {task.task_name}"

            # 使用自定义正文或默认正文
            if email_template.get('content'):
                # 替换模板变量
                content_text = email_template['content']
                content_text = content_text.replace('{teacher_name}', teacher.name)
                content_text = content_text.replace('{task_name}', task.task_name)
                if task.end_time:
                    content_text = content_text.replace('{end_time}', task.end_time.strftime('%Y-%m-%d'))
                else:
                    content_text = content_text.replace('{end_time}', '未设置')

                # 转换为HTML格式
                content = f"""
                <html>
                <body>
                    <div style="font-family: Arial, sans-serif; line-height: 1.6;">
                        {content_text.replace(chr(10), '<br>')}
                    </div>
                </body>
                </html>
                """
            else:
                # 默认邮件内容
                content = f"""
                <html>
                <body>
                    <h3>尊敬的{teacher.name}老师：</h3>
                    <p>您有一个新的科研任务需要处理：</p>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                        <p><strong>任务名称：</strong>{task.task_name}</p>
                        <p><strong>开始时间：</strong>{task.start_time.strftime('%Y-%m-%d %H:%M')}</p>
                        <p><strong>截止时间：</strong>{task.end_time.strftime('%Y-%m-%d %H:%M') if task.end_time else '未设置'}</p>
                        <p><strong>提醒时间：</strong>{task.reminder_time.strftime('%Y-%m-%d %H:%M') if task.reminder_time else '未设置'}</p>
                    </div>
                    <p>请及时登录系统查看并完成任务。</p>
                    <p><em>科研管理系统</em></p>
                </body>
                </html>
                """

            # 发送邮件
            success, message = mail_client.send_task_email(
                teacher.email, subject, content, attachment_path
            )

            print(f"收件人: {teacher.email}")
            print(f"邮件主题: {subject}")
            print(f"附件路径: {attachment_path}")
            print(f"邮件内容长度: {len(content)} 字符")

            if success:
                success_count += 1
                recipient.sent_time = datetime.now()
            else:
                fail_count += 1
                flash(f'发送给 {teacher.name} 的邮件失败: {message}', 'warning')

        db.session.commit()

        if success_count > 0:
            flash(f'任务通知发送完成！成功: {success_count} 封，失败: {fail_count} 封', 'success')
        else:
            flash('所有邮件发送都失败了，请检查邮件配置', 'error')

    except Exception as e:
        db.session.rollback()
        flash(f'发送失败: {str(e)}', 'error')

    return redirect(url_for('task_center'))



# 创建新任务
@app.route('/create_task', methods=['POST'])
def create_task():
    try:
        # 1. 获取隐藏域 ID，判断是“新建”还是“更新”
        task_id = request.form.get('existing_task_id')

        if task_id:
            # === 更新模式 (编辑草稿) ===
            task = Task.query.get_or_404(task_id)
            print(f"正在更新草稿: {task_id}")

            # 如果之前有上传过文件，且这次上传了新文件，可以考虑删除旧文件（可选）
            if 'format_file' in request.files:
                file = request.files['format_file']
                if file and file.filename != '':
                    # 这里简单的逻辑是：只要传了新文件，就覆盖旧路径
                    pass
        else:
            # === 新建模式 ===
            print("正在创建新任务")
            task = Task(start_time=datetime.now())
            db.session.add(task)

        # 2. 更新通用字段 (无论是新建还是更新，都执行这些赋值)
        task.task_name = request.form['task_name']

        # 处理时间
        if request.form.get('end_time'):
            task.end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%d')
        if request.form.get('reminder_time'):
            task.reminder_time = datetime.strptime(request.form['reminder_time'], '%Y-%m-%d')

        # 保存邮件内容到数据库
        task.email_subject = request.form.get('email_subject', '')
        task.email_content = request.form.get('email_content', '')

        # 3. 处理文件上传
        if 'format_file' in request.files:
            file = request.files['format_file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                task.format_file = filename  # 更新数据库里的文件名

        # 4. 确定状态
        save_as_draft = request.form.get('save_as_draft') == '1'
        task.status = 'draft' if save_as_draft else 'active'

        # 5. 处理收件人 (重置逻辑)
        # 如果是更新草稿，收件人范围可能变了，最简单的做法是：先删除旧的关联，再重新添加
        if task_id:
            TaskRecipient.query.filter_by(task_id=task.task_id).delete()

        # 提交一次以确保 task.task_id 生成（如果是新建）
        db.session.commit()

        # --- 重新计算并添加收件人 ---
        recipient_type = request.form.get('recipient_type', 'all')
        teacher_ids = []

        if recipient_type == 'all':
            teachers = Teacher.query.all()
            teacher_ids = [t.teacher_id for t in teachers]
        elif recipient_type == 'department':
            dep_id = request.form.get('department')
            teachers = Teacher.query.filter_by(dep_id=dep_id).all()
            teacher_ids = [t.teacher_id for t in teachers]
        elif recipient_type == 'manual':
            teacher_ids = request.form.getlist('recipients')

        # 写入 TaskRecipient 表
        for tid in teacher_ids:
            recipient = TaskRecipient(
                task_id=task.task_id,
                teacher_id=tid,
                sent_time=None
            )
            db.session.add(recipient)

        db.session.commit()

        # 6. 如果不是草稿，立即发送邮件
        if not save_as_draft:
            send_task_emails(task.task_id)  # 调用你已有的发送函数
            flash(f'任务已发布！邮件已发送给 {len(teacher_ids)} 人', 'success')
        else:
            flash(f'草稿保存成功！已记录 {len(teacher_ids)} 名收件人', 'info')

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()  # 在控制台打印详细错误
        flash(f'操作失败: {str(e)}', 'error')

    return redirect(url_for('task_center'))



# 查看任务详情
@app.route('/task_detail/<int:task_id>')
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    recipients = TaskRecipient.query.filter_by(task_id=task_id).all()
    return render_template('task_detail.html', task=task, recipients=recipients)


# 文件回收管理
@app.route('/recycled_files')
def recycled_files():
    files = RecycledExcel.query.order_by(RecycledExcel.upload_time.desc()).all()
    return render_template('recycled_files.html', files=files)


# 下载模板文件
@app.route('/download_template/<int:task_id>')
def download_template(task_id):
    task = Task.query.get_or_404(task_id)
    if task.format_file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], task.format_file)
        return send_file(file_path, as_attachment=True,
                         download_name=f"任务模板_{task.task_name}.xlsx")
    else:
        flash('该任务没有模板文件', 'error')
        return redirect(url_for('task_center'))


# 更新任务状态
@app.route('/update_task_status/<int:task_id>', methods=['POST'])
def update_task_status(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        new_status = request.form.get('status')
        
        if new_status not in ['draft', 'active', 'completed', 'cancelled']:
            flash('无效的任务状态', 'error')
            return redirect(url_for('task_center'))
        
        task.status = new_status
        db.session.commit()
        flash('任务状态更新成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'更新失败: {str(e)}', 'error')

    return redirect(url_for('task_center'))


# 删除任务
@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        
        # 先删除关联的接收者记录
        TaskRecipient.query.filter_by(task_id=task_id).delete()
        
        # 删除关联的回收文件记录
        RecycledExcel.query.filter_by(task_id=task_id).delete()
        
        # 删除任务文件（如果存在）
        if task.format_file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], task.format_file)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass  # 如果文件删除失败，继续删除数据库记录
        
        # 删除任务
        db.session.delete(task)
        db.session.commit()
        
        flash('任务删除成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'error')
    
    return redirect(url_for('task_center'))


# 获取任务收件人统计（AJAX接口）
@app.route('/api/task/<int:task_id>/recipients')
def get_task_recipients(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        recipients = TaskRecipient.query.filter_by(task_id=task_id).all()
        
        total = len(recipients)
        replied = len([r for r in recipients if r.is_replied])
        not_replied = total - replied
        
        return jsonify({
            'success': True,
            'total': total,
            'replied': replied,
            'not_replied': not_replied,
            'reply_rate': round((replied / total * 100) if total > 0 else 0, 2)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



if __name__ == '__main__':
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5000)