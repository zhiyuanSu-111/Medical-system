from flask import Flask, request, jsonify, g
from flask_cors import CORS
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import URLSafeTimedSerializer
import json
import os
import base64
import time
from datetime import datetime, timedelta
from openai import OpenAI
from config import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    DASHSCOPE_MODEL,
    DASHSCOPE_VISION_MODEL,
    DASHSCOPE_MAX_TOKENS,
    DASHSCOPE_TEMPERATURE,
    validate_api_key
)
from database import (
    get_db_connection,
    init_database,
    ensure_hospital_departments_seeded,
    next_doctor_business_id_for_department,
    is_outpatient_slot_day_for_doctor,
    get_default_slot_count_for_doctor,
    seed_appointment_slots_for_doctor,
    reconcile_appointment_slot_booked_counts,
    normalize_appointment_slot_half_day_totals_for_doctor,
    normalize_appointment_slot_half_day_totals,
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-medical-system-secret-key-change-me')
CORS(app)


def _auth_serializer():
    return URLSafeTimedSerializer(app.config['SECRET_KEY'], salt='medical-auth-v1')


def create_auth_token(user_id):
    return _auth_serializer().dumps({'uid': int(user_id)})


def parse_auth_token(token):
    try:
        data = _auth_serializer().loads(token, max_age=7 * 24 * 3600)
        return int(data['uid'])
    except Exception:
        return None


def _user_row_to_dict(row):
    if not row:
        return None
    return {
        'id': row['id'],
        'username': row['username'],
        'role': row['role'],
        'doctorBusinessId': row['doctor_business_id'],
        'displayName': (row['display_name'] or row['username'] or '').strip(),
    }


def fetch_user_by_id(uid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, username, role, doctor_business_id, display_name FROM users WHERE id = ?',
        (uid,),
    )
    row = cursor.fetchone()
    conn.close()
    return _user_row_to_dict(row)


def get_request_user():
    auth = request.headers.get('Authorization', '') or ''
    if not auth.startswith('Bearer '):
        return None
    uid = parse_auth_token(auth[7:].strip())
    if uid is None:
        return None
    return fetch_user_by_id(uid)


def require_roles(*roles):
    def decorator(fn):
        @wraps(fn)
        def inner(*a, **kw):
            u = get_request_user()
            if not u:
                return jsonify({'status': 'error', 'message': '请先登录'}), 401
            if u['role'] not in roles:
                return jsonify({'status': 'error', 'message': '权限不足'}), 403
            g.auth_user = u
            return fn(*a, **kw)

        return inner

    return decorator


def _sqlite_row_to_dict(row):
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}


# 初始化数据库
init_database()


def normalize_appointment_slots():
    """
    与 database.get_default_slot_count_for_doctor 一致：total_count 为「每个半日时段」上限。
    - 专家号：每段 20，全天两时段合计 40
    - 普通号：每段 40，全天两时段合计 80
    （此前旧逻辑误把「全天合计」当成每段上限，导致专家号在前端合计成 80。）
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        normalize_appointment_slot_half_day_totals(cursor)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"警告：规范化号源总数失败：{e}")


# 应用启动时修复历史错误号源并与患者端展示一致
normalize_appointment_slots()

# 验证并初始化阿里云百炼（DashScope）客户端
is_valid, validation_message = validate_api_key(DASHSCOPE_API_KEY)
if not is_valid:
    print(f"警告: {validation_message}")
    print(f"当前API密钥: {DASHSCOPE_API_KEY[:10]}...{DASHSCOPE_API_KEY[-4:] if len(DASHSCOPE_API_KEY) > 14 else ''}")
    print("请检查API密钥是否正确配置")

try:
    # 初始化阿里云百炼客户端
    client = OpenAI(
        api_key=DASHSCOPE_API_KEY,
        base_url=DASHSCOPE_BASE_URL
    )
    print(f"阿里云百炼（DashScope）客户端初始化成功")
    print(f"使用模型: {DASHSCOPE_MODEL}")
    print(f"API端点: {DASHSCOPE_BASE_URL}")
    print(f"API密钥长度: {len(DASHSCOPE_API_KEY)}")
except Exception as e:
    print(f"客户端初始化失败: {str(e)}")
    client = None

# 医疗助手系统提示词
MEDICAL_SYSTEM_PROMPT = """你是一位专业的AI医疗助手。你的职责是：
1. 耐心倾听患者的症状描述
2. 提供初步的健康建议和注意事项
3. 提醒患者如果症状严重或持续，应及时就医
4. 使用专业但易懂的语言
5. 不要给出具体的诊断或处方，只提供健康建议
6. 始终保持友好、关怀的态度
7. 你会收到完整对话记录：若患者已在上下文中说明不适部位、症状、时长等信息，必须据此作答；不要重复让对方从头描述，除非需要澄清矛盾或补充关键缺失信息。

请用中文回复，回复要简洁明了，控制在200字以内。"""

# 多轮对话中最多带入的历史条数（user/assistant 各算一条）
AI_HISTORY_MAX_MESSAGES = 40


def _parse_ai_history_param(raw):
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except Exception:
            return []
    return []


def _sanitize_ai_history(items):
    out = []
    for item in items[-AI_HISTORY_MAX_MESSAGES:]:
        if not isinstance(item, dict):
            continue
        role = item.get('role')
        content = (item.get('content') or '').strip()
        if role not in ('user', 'assistant') or not content:
            continue
        if len(content) > 8000:
            content = content[:8000] + '…'
        out.append({'role': role, 'content': content})
    return out

# AI问诊API
@app.route('/api/ai-consultation', methods=['POST'])
def ai_consultation():
    try:
        # 同时兼容 JSON 和 multipart/form-data（带文件）的请求
        message = ''
        uploaded_file = None

        content_type = request.content_type or ''
        history = []
        if 'multipart/form-data' in content_type.lower():
            # 前端使用 FormData 提交
            message = request.form.get('message', '') or ''
            uploaded_file = request.files.get('file')
            history = _sanitize_ai_history(_parse_ai_history_param(request.form.get('history')))
        else:
            # 传统 JSON 提交
            data = request.get_json(silent=True) or {}
            message = data.get('message', '') or ''
            history = _sanitize_ai_history(_parse_ai_history_param(data.get('history')))

        # 仅允许上传图片（防止前端 accept 被绕过）
        if uploaded_file:
            filename = (uploaded_file.filename or '').lower()
            allowed_ext = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp')
            content_type = (uploaded_file.mimetype or '').lower()
            is_image_mime = content_type.startswith('image/')
            is_allowed_ext = filename.endswith(allowed_ext)
            if not (is_image_mime or is_allowed_ext):
                return jsonify({
                    'response': '目前仅支持上传图片（png/jpg/jpeg/webp/gif/bmp）。',
                    'status': 'error'
                }), 400
        
        if not message and not uploaded_file:
            return jsonify({
                'response': '请输入您的问题或症状描述，或上传相关资料。',
                'status': 'error'
            }), 400

        # 仅允许图片上传（防止非图片文件）
        if uploaded_file is not None and uploaded_file.filename:
            mimetype = (uploaded_file.mimetype or '').lower()
            if not mimetype.startswith('image/'):
                return jsonify({
                    'response': '仅支持上传图片文件（jpg/png/webp等）。',
                    'status': 'error'
                }), 400
        
        # 检查客户端是否已初始化
        if client is None:
            return jsonify({
                'response': 'AI服务未正确初始化，请检查API密钥配置。',
                'status': 'error',
                'error': 'OpenAI client not initialized'
            }), 500

        # 调用阿里云百炼API
        try:
            # 如果带有图片，则使用多模态模型进行图片问诊；否则使用文本模型
            if uploaded_file:
                # 读取图片并编码为 data URL（适配 OpenAI 兼容协议的 image_url 形式）
                img_bytes = uploaded_file.read()
                mime_type = (uploaded_file.mimetype or "image/png").lower()
                b64_data = base64.b64encode(img_bytes).decode("utf-8")
                data_url = f"data:{mime_type};base64,{b64_data}"

                model_name = DASHSCOPE_VISION_MODEL
                messages = [{"role": "system", "content": MEDICAL_SYSTEM_PROMPT}]
                for h in history:
                    messages.append({"role": h['role'], "content": h['content']})
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url
                                },
                            },
                            {
                                "type": "text",
                                "text": message or "请结合这张图片进行分析，并给出健康建议。"
                            },
                        ],
                    }
                )
                # 图片问诊场景通常不需要太长的文本输出，max_tokens 可复用全局配置
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                )
            else:
                model_name = DASHSCOPE_MODEL
                messages = [{"role": "system", "content": MEDICAL_SYSTEM_PROMPT}]
                for h in history:
                    messages.append({"role": h['role'], "content": h['content']})
                messages.append({"role": "user", "content": message})
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=DASHSCOPE_TEMPERATURE,
                    max_tokens=DASHSCOPE_MAX_TOKENS,
                )
            
            response_text = response.choices[0].message.content.strip()
            
            return jsonify({
                'response': response_text,
                'status': 'success'
            })
            
        except Exception as e:
            # 如果API调用失败，返回详细的错误信息用于调试
            error_msg = str(e)
            error_type = type(e).__name__
            print(f"阿里云百炼API错误: {error_msg}")
            print(f"错误类型: {error_type}")
            
            # 根据错误类型返回不同的提示
            if "authentication" in error_msg.lower() or "api key" in error_msg.lower() or "401" in error_msg or "invalid_api_key" in error_msg.lower() or "unauthorized" in error_msg.lower():
                error_response = 'API密钥验证失败。请检查：\n1. API密钥是否正确（应以sk-开头）\n2. API密钥是否有效且有余额\n3. 是否已开通阿里云百炼服务'
            elif "Connection" in error_msg or "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                error_response = '网络连接失败，无法连接到AI服务。请检查网络连接或稍后重试。'
            elif "rate limit" in error_msg.lower() or "429" in error_msg:
                error_response = '请求过于频繁，请稍后再试。'
            elif "insufficient_quota" in error_msg.lower() or "quota" in error_msg.lower() or "余额" in error_msg:
                error_response = 'API配额不足，请检查账户余额。'
            else:
                error_response = f'AI服务错误: {error_msg[:150]}'
            
            return jsonify({
                'response': error_response,
                'status': 'error',
                'error': error_msg,
                'error_type': error_type
            }), 500
            
    except Exception as e:
        return jsonify({
            'response': '服务器错误，请稍后再试。',
            'status': 'error',
            'error': str(e)
        }), 500


# 获取医生号源信息
@app.route('/api/appointment-slots', methods=['GET'])
def get_appointment_slots():
    """获取指定医生在指定日期的号源信息"""
    doctor_id = request.args.get('doctor_id', type=int)
    date = request.args.get('date')
    
    if not doctor_id or not date:
        return jsonify({
            'status': 'error',
            'message': '缺少必要参数：doctor_id 和 date'
        }), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        reconcile_appointment_slot_booked_counts(cursor, doctor_business_id=doctor_id)
        conn.commit()

        # 查询号源信息
        cursor.execute('''
            SELECT time_slot, total_count, booked_count, 
                   (total_count - booked_count) as available_count
            FROM appointment_slots
            WHERE doctor_id = ? AND date = ?
            ORDER BY time_slot
        ''', (doctor_id, date))
        
        slots = []
        for row in cursor.fetchall():
            slots.append({
                'time_slot': row['time_slot'],
                'total_count': row['total_count'],
                'booked_count': row['booked_count'],
                'available_count': row['available_count']
            })
        
        conn.close()
        conn = None
        
        return jsonify({
            'status': 'success',
            'slots': slots
        })
    except Exception as e:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        return jsonify({
            'status': 'error',
            'message': f'查询号源失败: {str(e)}'
        }), 500

# 挂号API
@app.route('/api/appointment', methods=['POST'])
def appointment():
    """创建预约并扣减号源"""
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        data = {}

    # 验证必要字段
    required_fields = ['doctor', 'date', 'timeSlot', 'patientName', 'patientPhone', 'patientIdCard']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'status': 'error',
                'message': f'缺少必要字段: {field}'
            }), 400

    auth_user = get_request_user()
    if not auth_user or auth_user.get('role') != 'patient':
        return jsonify({
            'status': 'error',
            'message': '请以患者身份登录后再提交预约'
        }), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取医生ID（从医生姓名匹配，实际应该用doctor_id）
        doctor_name = data.get('doctor')
        doctor_title = data.get('doctorTitle', '')
        
        # 查找医生（优先通过传入的 doctorId，确保前后端 doctorId 一致）
        doctor_db_id = None
        doctor_id = None
        
        payload_doctor_id = data.get('doctorId')
        if payload_doctor_id is not None:
            # 前端传入的 doctorId 直接作为业务 doctor_id 使用
            doctor_id = int(payload_doctor_id)
            cursor.execute('SELECT id, doctor_id FROM doctors WHERE doctor_id = ?', (doctor_id,))
            result = cursor.fetchone()
            if result:
                doctor_db_id = result['id']
            else:
                # 数据库中不存在该医生，按传入的 doctorId 创建记录
                cursor.execute('''
                    INSERT INTO doctors (doctor_id, name, title, specialty, department_id, sub_department_id, specialty_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    doctor_id,
                    doctor_name,
                    doctor_title,
                    data.get('specialty', ''),
                    data.get('departmentId'),
                    data.get('subDepartmentId'),
                    data.get('specialtyId')
                ))
                doctor_db_id = cursor.lastrowid
        else:
            # 如果没有传入 doctorId，尝试通过姓名匹配（仅用于兼容旧数据，实际应总是传 doctorId）
            cursor.execute('SELECT id, doctor_id FROM doctors WHERE name = ? LIMIT 1', (doctor_name,))
            result = cursor.fetchone()
            if result:
                doctor_db_id = result['id']
                doctor_id = result['doctor_id']
            else:
                # 无工号且无姓名匹配：优先按科室分配 6 位工号，否则退化为时间戳取模
                doctor_id = next_doctor_business_id_for_department(
                    cursor, data.get('departmentId')
                )
                if doctor_id is None:
                    doctor_id = int(time.time()) % 1_000_000
                cursor.execute('''
                    INSERT INTO doctors (doctor_id, name, title, specialty, department_id, sub_department_id, specialty_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    doctor_id,
                    doctor_name,
                    doctor_title,
                    data.get('specialty', ''),
                    data.get('departmentId'),
                    data.get('subDepartmentId'),
                    data.get('specialtyId')
                ))
                doctor_db_id = cursor.lastrowid
        
        # 检查号源是否可用
        date = data['date']
        time_slot = data['timeSlot']
        try:
            appt_date = datetime.strptime(date, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            conn.close()
            return jsonify({
                'status': 'error',
                'message': '就诊日期格式无效，请使用 YYYY-MM-DD'
            }), 400

        reconcile_appointment_slot_booked_counts(cursor, doctor_business_id=doctor_id)

        cursor.execute('''
            SELECT id, total_count, booked_count 
            FROM appointment_slots
            WHERE doctor_id = ? AND date = ? AND time_slot = ?
        ''', (doctor_id, date, time_slot))
        
        slot = cursor.fetchone()
        
        if not slot:
            if not is_outpatient_slot_day_for_doctor(doctor_id, appt_date):
                conn.close()
                return jsonify({
                    'status': 'error',
                    'message': '该日期非门诊出诊日（周末或该医生本周固定休诊日），请选择其他日期'
                }), 400
            # 如果号源不存在，按医生类型创建新号源：
            # 专家号每时段40个，普通号每时段80个
            default_total = get_default_slot_count_for_doctor(cursor, doctor_id, fallback=40)
            cursor.execute('''
                INSERT INTO appointment_slots (doctor_id, date, time_slot, total_count, booked_count)
                VALUES (?, ?, ?, ?, 0)
            ''', (doctor_id, date, time_slot, default_total))
            available_count = default_total
        else:
            available_count = slot['total_count'] - slot['booked_count']
        
        # 检查号源是否已满
        if available_count <= 0:
            conn.close()
            return jsonify({
                'status': 'error',
                'message': '该时段号源已满，请选择其他时段'
            }), 400

        # 生成预约号
        appointment_id = 'A' + str(int(time.time()))
        
        # 创建预约记录
        cursor.execute('''
            INSERT INTO appointments (
                appointment_id, doctor_id, date, time_slot,
                patient_name, patient_phone, patient_id_card,
                department, sub_department, specialty,
                doctor_name, doctor_title, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'confirmed')
        ''', (
            appointment_id, doctor_id, date, time_slot,
            data['patientName'], data['patientPhone'], data['patientIdCard'],
            data.get('department', ''), data.get('subDepartment', ''), data.get('specialty', ''),
            doctor_name, doctor_title
        ))
        reconcile_appointment_slot_booked_counts(cursor, doctor_business_id=doctor_id)

        conn.commit()
        conn.close()
        
        return jsonify({
            'appointmentId': appointment_id,
            'status': 'success',
            'message': '预约成功'
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({
            'status': 'error',
            'message': f'预约失败: {str(e)}'
        }), 500

# 获取科室列表（来自数据库，管理员可维护）
@app.route('/api/departments', methods=['GET'])
def get_departments():
    try:
        ensure_hospital_departments_seeded()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, icon FROM hospital_departments ORDER BY id')
        rows = cursor.fetchall()
        conn.close()
        departments = [
            {'id': r['id'], 'name': r['name'], 'icon': r['icon'] or '🏥'} for r in rows
        ]
        return jsonify({'departments': departments})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e), 'departments': []}), 500


RESERVED_USERNAMES = frozenset({'admin', 'doctor', 'root', 'system'})


@app.route('/api/auth/register', methods=['POST'])
def auth_register():
    """患者注册"""
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    display_name = (data.get('displayName') or username).strip() or username
    if len(username) < 3:
        return jsonify({'status': 'error', 'message': '用户名至少 3 个字符'}), 400
    if len(password) < 4:
        return jsonify({'status': 'error', 'message': '密码至少 4 个字符'}), 400
    if username.lower() in RESERVED_USERNAMES:
        return jsonify({'status': 'error', 'message': '该用户名不可用'}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'status': 'error', 'message': '用户名已存在'}), 400
        cursor.execute(
            '''
            INSERT INTO users (username, password_hash, role, doctor_business_id, display_name)
            VALUES (?, ?, 'patient', NULL, ?)
            ''',
            (username, generate_password_hash(password), display_name),
        )
        uid = cursor.lastrowid
        conn.commit()
        conn.close()
        user = fetch_user_by_id(uid)
        token = create_auth_token(uid)
        return jsonify({'status': 'success', 'token': token, 'user': user})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'注册失败: {str(e)}'}), 500


@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not username or not password:
        return jsonify({'status': 'error', 'message': '请输入用户名和密码'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, username, password_hash, role, doctor_business_id, display_name FROM users WHERE username = ?',
        (username,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row or not check_password_hash(row['password_hash'], password):
        return jsonify({'status': 'error', 'message': '用户名或密码错误'}), 401
    user = _user_row_to_dict(row)
    token = create_auth_token(row['id'])
    return jsonify({'status': 'success', 'token': token, 'user': user})


@app.route('/api/auth/me', methods=['GET'])
def auth_me():
    u = get_request_user()
    if not u:
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    return jsonify({'status': 'success', 'user': u})


@app.route('/api/doctor/my-schedule', methods=['GET'])
@require_roles('doctor')
def doctor_my_schedule():
    """当前登录医生查看本人号源与近期预约"""
    bid = g.auth_user.get('doctorBusinessId')
    if not bid:
        return jsonify({'status': 'error', 'message': '账号未绑定医生工号，请联系管理员'}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        reconcile_appointment_slot_booked_counts(cursor, doctor_business_id=bid)
        conn.commit()

        cursor.execute(
            '''
            SELECT name, title, specialty, department_id, sub_department_id
            FROM doctors WHERE doctor_id = ? LIMIT 1
            ''',
            (bid,),
        )
        doc = cursor.fetchone()
        cursor.execute(
            '''
            SELECT date, time_slot, total_count, booked_count,
                   (total_count - booked_count) AS available_count
            FROM appointment_slots
            WHERE doctor_id = ?
            ORDER BY date, time_slot
            ''',
            (bid,),
        )
        slots = [_sqlite_row_to_dict(row) for row in cursor.fetchall()]
        cursor.execute(
            '''
            SELECT appointment_id, date, time_slot, patient_name, patient_phone, status, created_at
            FROM appointments
            WHERE doctor_id = ?
            ORDER BY date DESC, time_slot DESC
            LIMIT 200
            ''',
            (bid,),
        )
        appts = [_sqlite_row_to_dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({
            'status': 'success',
            'doctor': _sqlite_row_to_dict(doc) if doc else None,
            'doctorBusinessId': bid,
            'slots': slots,
            'appointments': appts,
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/admin/departments', methods=['GET'])
@require_roles('admin')
def admin_list_departments():
    ensure_hospital_departments_seeded()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, icon FROM hospital_departments ORDER BY id')
    rows = [_sqlite_row_to_dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({'status': 'success', 'departments': rows})


@app.route('/api/admin/departments', methods=['POST'])
@require_roles('admin')
def admin_create_department():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    icon = (data.get('icon') or '🏥').strip() or '🏥'
    if not name:
        return jsonify({'status': 'error', 'message': '科室名称不能为空'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS nid FROM hospital_departments')
    new_id = cursor.fetchone()['nid']
    cursor.execute(
        'INSERT INTO hospital_departments (id, name, icon) VALUES (?, ?, ?)',
        (new_id, name, icon),
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'id': new_id})


@app.route('/api/admin/departments/<int:dept_id>', methods=['PUT'])
@require_roles('admin')
def admin_update_department(dept_id):
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    icon = (data.get('icon') or '').strip()
    if not name:
        return jsonify({'status': 'error', 'message': '科室名称不能为空'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE hospital_departments SET name = ?, icon = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (name, icon or '🏥', dept_id),
    )
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'status': 'error', 'message': '科室不存在'}), 404
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})


@app.route('/api/admin/departments/<int:dept_id>', methods=['DELETE'])
@require_roles('admin')
def admin_delete_department(dept_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT COUNT(*) AS c FROM doctors WHERE department_id = ?',
        (dept_id,),
    )
    if cursor.fetchone()['c'] > 0:
        conn.close()
        return jsonify({'status': 'error', 'message': '仍有医生归属该科室，无法删除'}), 400
    cursor.execute('DELETE FROM hospital_departments WHERE id = ?', (dept_id,))
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'status': 'error', 'message': '科室不存在'}), 404
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})


@app.route('/api/admin/doctors', methods=['GET'])
@require_roles('admin')
def admin_list_doctors():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT id, doctor_id, name, title, specialty, department_id, sub_department_id, specialty_id, created_at
        FROM doctors ORDER BY id
        '''
    )
    rows = [_sqlite_row_to_dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({'status': 'success', 'doctors': rows})


@app.route('/api/admin/doctors', methods=['POST'])
@require_roles('admin')
def admin_create_doctor():
    data = request.get_json(silent=True) or {}
    doctor_id = data.get('doctorId')
    name = (data.get('name') or '').strip()
    title = (data.get('title') or '').strip() or '医师'
    specialty = (data.get('specialty') or '').strip() or '门诊'
    department_id = data.get('departmentId')
    sub_department_id = data.get('subDepartmentId')
    specialty_id = data.get('specialtyId')
    if doctor_id is None or not name:
        return jsonify({'status': 'error', 'message': '请填写医生工号与姓名'}), 400
    try:
        doctor_id = int(doctor_id)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': '医生工号必须为整数'}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO doctors (doctor_id, name, title, specialty, department_id, sub_department_id, specialty_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                doctor_id,
                name,
                title,
                specialty,
                department_id,
                sub_department_id,
                specialty_id,
            ),
        )
        rid = cursor.lastrowid
        seed_appointment_slots_for_doctor(cursor, doctor_id, days=21)
        normalize_appointment_slot_half_day_totals_for_doctor(cursor, doctor_id)
        reconcile_appointment_slot_booked_counts(cursor, doctor_business_id=doctor_id)
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'id': rid})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/admin/doctors/<int:row_id>', methods=['PUT'])
@require_roles('admin')
def admin_update_doctor(row_id):
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    title = (data.get('title') or '').strip()
    specialty = (data.get('specialty') or '').strip()
    if not name:
        return jsonify({'status': 'error', 'message': '姓名不能为空'}), 400
    try:
        doctor_id = int(data['doctorId'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'status': 'error', 'message': '请提供有效的医生工号 doctorId'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        UPDATE doctors SET doctor_id = ?, name = ?, title = ?, specialty = ?,
            department_id = ?, sub_department_id = ?, specialty_id = ?
        WHERE id = ?
        ''',
        (
            doctor_id,
            name,
            title or '医师',
            specialty or '门诊',
            data.get('departmentId'),
            data.get('subDepartmentId'),
            data.get('specialtyId'),
            row_id,
        ),
    )
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'status': 'error', 'message': '记录不存在'}), 404
    seed_appointment_slots_for_doctor(cursor, doctor_id, days=21)
    normalize_appointment_slot_half_day_totals_for_doctor(cursor, doctor_id)
    reconcile_appointment_slot_booked_counts(cursor, doctor_business_id=doctor_id)
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})


@app.route('/api/admin/doctors/<int:row_id>', methods=['DELETE'])
@require_roles('admin')
def admin_delete_doctor(row_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT doctor_id FROM doctors WHERE id = ?', (row_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'status': 'error', 'message': '记录不存在'}), 404
    business_id = row['doctor_id']
    cursor.execute('SELECT COUNT(*) AS c FROM appointments WHERE doctor_id = ?', (business_id,))
    if cursor.fetchone()['c'] > 0:
        conn.close()
        return jsonify({'status': 'error', 'message': '该医生已有预约记录，无法删除'}), 400
    cursor.execute('DELETE FROM appointment_slots WHERE doctor_id = ?', (business_id,))
    cursor.execute('DELETE FROM doctors WHERE id = ?', (row_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})


# 获取医生列表（与 doctors 表、号源排班一致，供患者挂号页使用）
@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    department_id = request.args.get('department_id', type=int)
    sub_department_id = request.args.get('sub_department_id', type=int)
    specialty_id = request.args.get('specialty_id', type=int)
    date_str = (request.args.get('date') or '').strip()

    if department_id is None:
        return jsonify({'status': 'error', 'message': '缺少参数 department_id', 'doctors': []}), 400

    appt_date = None
    if date_str:
        try:
            appt_date = datetime.strptime(date_str[:10], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            appt_date = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        where = ['department_id = ?']
        params = [department_id]
        # 传入 specialty_id 时仅返回该专科门诊下的医生，避免同一子科室下各专科共用「通用号源」导致列表重复。
        if specialty_id is not None and specialty_id > 0:
            where.append('specialty_id = ?')
            params.append(specialty_id)
        elif sub_department_id is not None and sub_department_id > 0:
            where.append('sub_department_id = ?')
            params.append(sub_department_id)

        cursor.execute(
            f'''
            SELECT DISTINCT doctor_id, name, title, specialty
            FROM doctors WHERE {" AND ".join(where)} ORDER BY doctor_id
            ''',
            params,
        )
        rows = cursor.fetchall()
        conn.close()
        # 患者端传入 date 时：仅返回该日有门诊排班的医生（与 is_outpatient_slot_day_for_doctor、预约校验一致）
        if appt_date is not None:
            rows = [
                r
                for r in rows
                if is_outpatient_slot_day_for_doctor(int(r['doctor_id']), appt_date)
            ]
        doctors = [
            {
                'id': int(r['doctor_id']),
                'name': r['name'],
                'title': r['title'],
                'specialty': r['specialty'],
            }
            for r in rows
        ]
        return jsonify({'status': 'success', 'doctors': doctors})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e), 'doctors': []}), 500

# 查询预约记录列表
@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    """查询预约记录列表，支持按预约创建时间 created_at 做时间筛选"""
    try:
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        patient_phone = request.args.get('patient_phone')  # 可选：按手机号筛选
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询SQL
        query = '''
            SELECT 
                appointment_id, doctor_id, date, time_slot,
                patient_name, patient_phone, patient_id_card,
                department, sub_department, specialty,
                doctor_name, doctor_title, status, created_at
            FROM appointments
            WHERE 1=1
        '''
        params = []
        
        # 时间筛选（按 created_at）：如果没有提供，默认查询近三个月
        if not start_date:
            three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            start_date = three_months_ago
        
        if start_date:
            query += ' AND DATE(created_at) >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND DATE(created_at) <= ?'
            params.append(end_date)
        
        # 按手机号筛选（可选）
        if patient_phone:
            query += ' AND patient_phone = ?'
            params.append(patient_phone)
        
        # 按创建时间倒序排列
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        
        appointments = []
        for row in cursor.fetchall():
            appointments.append({
                'appointment_id': row['appointment_id'],
                'doctor_id': row['doctor_id'],
                'date': row['date'],
                'time_slot': row['time_slot'],
                'patient_name': row['patient_name'],
                'patient_phone': row['patient_phone'],
                'patient_id_card': row['patient_id_card'],
                'department': row['department'],
                'sub_department': row['sub_department'],
                'specialty': row['specialty'],
                'doctor_name': row['doctor_name'],
                'doctor_title': row['doctor_title'],
                'status': row['status'],
                'created_at': row['created_at']
            })
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'appointments': appointments,
            'count': len(appointments)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'查询预约记录失败: {str(e)}'
        }), 500

# 取消预约
@app.route('/api/appointments/<appointment_id>/cancel', methods=['POST'])
def cancel_appointment(appointment_id):
    """取消预约"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询预约记录
        cursor.execute('''
            SELECT doctor_id, date, time_slot, status
            FROM appointments
            WHERE appointment_id = ?
        ''', (appointment_id,))
        
        appointment = cursor.fetchone()
        
        if not appointment:
            conn.close()
            return jsonify({
                'status': 'error',
                'message': '预约记录不存在'
            }), 404
        
        # 检查是否已经取消
        if appointment['status'] == 'cancelled':
            conn.close()
            return jsonify({
                'status': 'error',
                'message': '该预约已经取消'
            }), 400
        
        # 更新预约状态为已取消
        cursor.execute('''
            UPDATE appointments
            SET status = 'cancelled'
            WHERE appointment_id = ?
        ''', (appointment_id,))

        doctor_id = appointment['doctor_id']
        # 按「已确认」预约重算号源占用，与排班页、患者端剩余号源一致
        reconcile_appointment_slot_booked_counts(cursor, doctor_business_id=doctor_id)

        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': '预约已成功取消'
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({
            'status': 'error',
            'message': f'取消预约失败: {str(e)}'
        }), 500

# 删除预约记录
@app.route('/api/appointments/<appointment_id>', methods=['DELETE'])
def delete_appointment(appointment_id):
    """删除预约记录（仅允许删除已取消的预约）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询预约记录
        cursor.execute('''
            SELECT status
            FROM appointments
            WHERE appointment_id = ?
        ''', (appointment_id,))
        
        appointment = cursor.fetchone()
        
        if not appointment:
            conn.close()
            return jsonify({
                'status': 'error',
                'message': '预约记录不存在'
            }), 404
        
        # 只允许删除已取消的预约
        if appointment['status'] != 'cancelled':
            conn.close()
            return jsonify({
                'status': 'error',
                'message': '只能删除已取消的预约记录'
            }), 400
        
        # 删除预约记录
        cursor.execute('''
            DELETE FROM appointments
            WHERE appointment_id = ?
        ''', (appointment_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': '预约记录已删除'
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({
            'status': 'error',
            'message': f'删除预约记录失败: {str(e)}'
        }), 500

# ==================== 就诊人管理 API ====================

# 获取所有就诊人
@app.route('/api/patients', methods=['GET'])
def get_patients():
    """获取所有就诊人列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, phone, id_card, created_at, updated_at
            FROM patients
            ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        patients = []
        for row in rows:
            patients.append({
                'id': row['id'],
                'name': row['name'],
                'phone': row['phone'],
                'idCard': row['id_card'],
                'createdAt': row['created_at'],
                'updatedAt': row['updated_at']
            })
        
        conn.close()
        return jsonify({
            'status': 'success',
            'data': patients
        })
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({
            'status': 'error',
            'message': f'获取就诊人列表失败: {str(e)}'
        }), 500

# 创建就诊人
@app.route('/api/patients', methods=['POST'])
def create_patient():
    """创建新就诊人"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        id_card = data.get('idCard', '').strip()
        
        if not name or not phone or not id_card:
            return jsonify({
                'status': 'error',
                'message': '请完整填写姓名、手机号和身份证号'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查身份证号是否已存在
        cursor.execute('SELECT id FROM patients WHERE id_card = ?', (id_card,))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                'status': 'error',
                'message': '该身份证号已存在'
            }), 400
        
        # 插入新就诊人
        cursor.execute('''
            INSERT INTO patients (name, phone, id_card)
            VALUES (?, ?, ?)
        ''', (name, phone, id_card))
        
        patient_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': '就诊人创建成功',
            'data': {
                'id': patient_id,
                'name': name,
                'phone': phone,
                'idCard': id_card
            }
        }), 201
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({
            'status': 'error',
            'message': f'创建就诊人失败: {str(e)}'
        }), 500

# 更新就诊人
@app.route('/api/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    """更新就诊人信息"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        id_card = data.get('idCard', '').strip()
        
        if not name or not phone or not id_card:
            return jsonify({
                'status': 'error',
                'message': '请完整填写姓名、手机号和身份证号'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查就诊人是否存在
        cursor.execute('SELECT id FROM patients WHERE id = ?', (patient_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'status': 'error',
                'message': '就诊人不存在'
            }), 404
        
        # 检查身份证号是否被其他就诊人使用
        cursor.execute('SELECT id FROM patients WHERE id_card = ? AND id != ?', (id_card, patient_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                'status': 'error',
                'message': '该身份证号已被其他就诊人使用'
            }), 400
        
        # 更新就诊人信息
        cursor.execute('''
            UPDATE patients
            SET name = ?, phone = ?, id_card = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (name, phone, id_card, patient_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': '就诊人信息更新成功',
            'data': {
                'id': patient_id,
                'name': name,
                'phone': phone,
                'idCard': id_card
            }
        })
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({
            'status': 'error',
            'message': f'更新就诊人信息失败: {str(e)}'
        }), 500

# 删除就诊人
@app.route('/api/patients/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    """删除就诊人"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查就诊人是否存在
        cursor.execute('SELECT id FROM patients WHERE id = ?', (patient_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'status': 'error',
                'message': '就诊人不存在'
            }), 404
        
        # 删除就诊人
        cursor.execute('DELETE FROM patients WHERE id = ?', (patient_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': '就诊人已删除'
        })
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({
            'status': 'error',
            'message': f'删除就诊人失败: {str(e)}'
        }), 500

# ==================== AI对话历史管理 API ====================

# 获取所有对话历史
@app.route('/api/consultation-history', methods=['GET'])
def get_consultation_history():
    """获取所有AI对话历史（最多50条，按更新时间倒序）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, conversation_id, title, messages, created_at, updated_at
            FROM consultation_history
            ORDER BY updated_at DESC
            LIMIT 50
        ''')
        
        rows = cursor.fetchall()
        history = []
        for row in rows:
            try:
                messages = json.loads(row['messages']) if row['messages'] else []
            except:
                messages = []
            
            history.append({
                'id': row['conversation_id'],
                'title': row['title'] or '',
                'messages': messages,
                'createdAt': row['created_at'],
                'updatedAt': row['updated_at']
            })
        
        conn.close()
        return jsonify({
            'status': 'success',
            'data': history
        })
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({
            'status': 'error',
            'message': f'获取对话历史失败: {str(e)}'
        }), 500

# 保存或更新对话历史
@app.route('/api/consultation-history', methods=['POST'])
def save_consultation_history():
    """保存或更新AI对话历史"""
    try:
        data = request.get_json()
        conversation_id = data.get('id')
        title = data.get('title', '').strip()
        messages = data.get('messages', [])
        
        if not conversation_id:
            return jsonify({
                'status': 'error',
                'message': '缺少对话ID'
            }), 400
        
        if not isinstance(messages, list):
            return jsonify({
                'status': 'error',
                'message': '消息格式错误'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 如果没有标题，使用第一条用户消息的前20个字符作为标题
        if not title and len(messages) > 0:
            first_user_message = next((m for m in messages if m.get('type') == 'user'), None)
            if first_user_message:
                text = first_user_message.get('text', '')
                if len(text) > 20:
                    title = text[:20] + '...'
                else:
                    title = text
        
        messages_json = json.dumps(messages, ensure_ascii=False)
        
        # 检查对话是否已存在
        cursor.execute('SELECT id FROM consultation_history WHERE conversation_id = ?', (conversation_id,))
        existing = cursor.fetchone()
        
        if existing:
            # 更新现有对话
            cursor.execute('''
                UPDATE consultation_history
                SET title = ?, messages = ?, updated_at = CURRENT_TIMESTAMP
                WHERE conversation_id = ?
            ''', (title, messages_json, conversation_id))
        else:
            # 创建新对话
            cursor.execute('''
                INSERT INTO consultation_history (conversation_id, title, messages)
                VALUES (?, ?, ?)
            ''', (conversation_id, title, messages_json))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': '对话历史保存成功'
        })
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({
            'status': 'error',
            'message': f'保存对话历史失败: {str(e)}'
        }), 500

# 删除对话历史
@app.route('/api/consultation-history/<conversation_id>', methods=['DELETE'])
def delete_consultation_history(conversation_id):
    """删除指定的AI对话历史"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查对话是否存在
        cursor.execute('SELECT id FROM consultation_history WHERE conversation_id = ?', (conversation_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'status': 'error',
                'message': '对话记录不存在'
            }), 404
        
        # 删除对话
        cursor.execute('DELETE FROM consultation_history WHERE conversation_id = ?', (conversation_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': '对话记录已删除'
        })
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({
            'status': 'error',
            'message': f'删除对话记录失败: {str(e)}'
        }), 500

# 初始化医生号源（管理接口）
@app.route('/api/init-slots', methods=['POST'])
@require_roles('admin')
def init_slots():
    """为指定医生初始化未来N天的号源"""
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    days = data.get('days', 7)  # 默认初始化7天
    total_count = data.get('total_count', 10)  # 每个时段默认10个号
    
    if not doctor_id:
        return jsonify({
            'status': 'error',
            'message': '缺少doctor_id参数'
        }), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查医生是否存在
        cursor.execute('SELECT id FROM doctors WHERE doctor_id = ?', (doctor_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'status': 'error',
                'message': '医生不存在'
            }), 404
        
        time_slots = ['08:00-12:00', '14:00-18:00']
        
        today = datetime.now().date()
        created_count = 0
        
        # 专家号每半日 20、普通号每半日 40（与 get_default_slot_count_for_doctor 一致）
        adjusted_total_count = get_default_slot_count_for_doctor(cursor, doctor_id, fallback=40)

        for i in range(days):
            slot_date = today + timedelta(days=i + 1)
            if not is_outpatient_slot_day_for_doctor(doctor_id, slot_date):
                continue
            for time_slot in time_slots:
                cursor.execute('''
                    INSERT OR IGNORE INTO appointment_slots (doctor_id, date, time_slot, total_count, booked_count)
                    VALUES (?, ?, ?, ?, 0)
                ''', (doctor_id, slot_date.strftime('%Y-%m-%d'), time_slot, adjusted_total_count))
                if cursor.rowcount > 0:
                    created_count += 1

        normalize_appointment_slot_half_day_totals_for_doctor(cursor, doctor_id)
        reconcile_appointment_slot_booked_counts(cursor, doctor_business_id=doctor_id)

        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'成功初始化{created_count}个号源时段'
        })
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({
            'status': 'error',
            'message': f'初始化失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    # 监听所有网卡地址，便于同局域网手机访问
    app.run(debug=True, host='0.0.0.0', port=5000)
