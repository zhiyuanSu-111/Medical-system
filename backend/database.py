"""
数据库模型和初始化
"""
import sqlite3
import os
from collections import defaultdict
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash

from specialty_clinic_seed import SPECIALTY_CLINIC_SEED

# 数据库文件路径（相对于backend目录）
DB_PATH = os.path.join(os.path.dirname(__file__), 'medical_system.db')

# 与前端挂号目录一致的科室种子（可被管理员在后台修改）
HOSPITAL_DEPARTMENT_SEED = [
    (1, '内科', '🫀'),
    (2, '外科', '🔪'),
    (3, '多学科协作诊治', '👥'),
    (4, '感染病科', '🦠'),
    (5, '肿瘤科', '🎗️'),
    (6, '耳鼻咽喉科', '👂'),
    (7, '眼科', '👁️'),
    (8, '口腔科', '🦷'),
    (9, '妇产科', '👩'),
    (10, '生殖医学', '👶'),
    (11, '儿科', '🧒'),
    (12, '变态反应（过敏）科', '🤧'),
    (13, '皮肤科', '🧴'),
    (14, '精神科卫生科', '🧠'),
    (15, '中医科', '🌿'),
    (16, '麻醉科', '💉'),
    (17, '医学影像科', '📷'),
    (18, '疼痛科', '😣'),
    (19, '医疗美容科', '✨'),
    (20, '全科医疗科', '🏥'),
    (21, '康复医学科', '🔄'),
    (22, '病理科', '🔬'),
    (23, '营养科', '🥗'),
    (24, '临床医学', '📋'),
    (25, '专科护理', '💊'),
    (26, '高压氧', '💨'),
    (27, '资深专家门诊', '👨‍⚕️'),
    (28, '我的收藏', '⭐'),
]

def doctor_business_id(department_id: int, sequence: int = 1) -> int:
    """
    统一 6 位医生工号：100000 + 科室ID(1–99)×100 + 科内序号(1–999)。
    示例：1 号科室首位 100101；2 号科室首位 100201；27 号科室首位 102701。
    序号上限 999，便于同一顶层科室下多子科室/专科演示数据不溢出。
    """
    if not (1 <= department_id <= 99) or not (1 <= sequence <= 999):
        raise ValueError('department_id 须在 1..99，sequence 须在 1..999')
    return 100_000 + department_id * 100 + sequence


def next_doctor_business_id_for_department(cursor, department_id):
    """
    在 [100000+科室×100+1, 100000+科室×100+999] 内取当前未使用的下一个工号。
    科室无效或已满时返回 None。
    """
    if department_id is None:
        return None
    try:
        d = int(department_id)
    except (TypeError, ValueError):
        return None
    if d < 1 or d > 99:
        return None
    lo = 100_000 + d * 100 + 1
    hi = 100_000 + d * 100 + 999
    cursor.execute(
        'SELECT MAX(doctor_id) AS m FROM doctors WHERE doctor_id BETWEEN ? AND ?',
        (lo, hi),
    )
    row = cursor.fetchone()
    m = row['m'] if row else None
    if m is None or m < lo:
        return lo
    if m >= hi:
        return None
    return int(m) + 1


# 迁移标记：将历史 <100000 的业务工号及 users 中 101 等旧值一次性对齐到 6 位规则
BUSINESS_ID_6DIGIT_MIGRATION_KEY = 'doctor_business_id_6digit_v1'


# 与「医生」登录账号绑定的演示工号（内科首位）
DEMO_DOCTOR_BUSINESS_ID = doctor_business_id(1, 1)

def _demo_person_name(idx: int) -> str:
    """生成不重复的演示姓名（同一目录内按序递增即可）。"""
    surnames = (
        '赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳'
    )
    given = '景思慕书予谨乐童念听雨远宁岚澈温润朗澈澄泓筠瑶昕昱珩珂玥玮琛琦璟瑜妍婉娴婧棠楠梓岑屿'
    return surnames[idx % len(surnames)] + given[(idx // len(surnames)) % len(given)]


def _build_demo_doctor_body():
    """
    每行 (姓名, 职称, 专科展示名, department_id, sub_department_id, specialty_id)。
    与前端专科门诊一一对应：每条专科至少 2 人，specialty 字段为真实门诊名称；专科 ID 与前端 specialtyId 一致。
    """
    rows = []
    ni = 0

    for dept_id, sub_raw, spec_id, label in SPECIALTY_CLINIC_SEED:
        sub_id = sub_raw if sub_raw else None
        if dept_id == 25:
            title_pair = ('主任护师', '主管护师')
        elif dept_id == 24:
            title_pair = ('主任药师', '主管药师')
        elif dept_id == 23:
            title_pair = ('主任营养师', '副主任营养师')
        else:
            title_pair = ('主任医师', '副主任医师')

        for title in title_pair:
            if dept_id == 1 and spec_id == 1 and title == '主任医师':
                name = '周景明'
            else:
                name = _demo_person_name(ni)
            ni += 1
            rows.append((name, title, label, dept_id, sub_id, spec_id))

    return rows


_FULL_DOCTOR_BODY = _build_demo_doctor_body()


def _make_full_doctor_catalog():
    seq_by_dept = {}
    out = []
    for name, title, spec, d, sub, sid in _FULL_DOCTOR_BODY:
        seq_by_dept[d] = seq_by_dept.get(d, 0) + 1
        bid = doctor_business_id(d, seq_by_dept[d])
        out.append((bid, name, title, spec, d, sub, sid))
    return out


FULL_DOCTOR_CATALOG = _make_full_doctor_catalog()

DOCTOR_CATALOG_VERSION = '7'
CATALOG_SKIPPED_APPTS = '7-skipped-existing-appts'
# 旧版跳过标记（无预约后仍可重新灌目录）
_LEGACY_SKIPPED = ('3-skipped-existing-appts',)

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
    return conn

def init_database():
    """初始化数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建医生表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            specialty TEXT NOT NULL,
            department_id INTEGER,
            sub_department_id INTEGER,
            specialty_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(doctor_id, specialty_id)
        )
    ''')
    
    # 创建号源表（医生+日期+时段）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointment_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            date DATE NOT NULL,
            time_slot TEXT NOT NULL,
            total_count INTEGER DEFAULT 10,
            booked_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(doctor_id, date, time_slot),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    ''')
    
    # 创建预约记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id TEXT UNIQUE NOT NULL,
            doctor_id INTEGER NOT NULL,
            date DATE NOT NULL,
            time_slot TEXT NOT NULL,
            patient_name TEXT NOT NULL,
            patient_phone TEXT NOT NULL,
            patient_id_card TEXT NOT NULL,
            department TEXT,
            sub_department TEXT,
            specialty TEXT,
            doctor_name TEXT,
            doctor_title TEXT,
            status TEXT DEFAULT 'confirmed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    ''')
    
    # 创建就诊人表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            id_card TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(id_card)
        )
    ''')
    
    # 创建AI对话历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consultation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT UNIQUE NOT NULL,
            title TEXT,
            messages TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建索引以提高查询性能
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_slots_doctor_date ON appointment_slots(doctor_id, date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_doctor_date ON appointments(doctor_id, date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id_card)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_consultation_history_updated ON consultation_history(updated_at DESC)')

    # 科室字典表（管理员可增删改查）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospital_departments (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT DEFAULT '🏥',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 用户表：患者 / 医生 / 管理员
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            doctor_business_id INTEGER,
            display_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CHECK (role IN ('patient', 'doctor', 'admin'))
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        '''
    )

    conn.commit()

    _seed_hospital_departments(cursor)
    _ensure_doctor_catalog(cursor, conn)
    _migrate_legacy_doctor_business_ids(cursor, conn)
    _seed_default_staff_users(cursor)
    _sync_demo_doctor_user_binding(cursor)
    backfill_appointment_slots_for_all_doctors(cursor, days=21)
    normalize_appointment_slot_half_day_totals(cursor)
    reconcile_appointment_slot_booked_counts(cursor)
    conn.commit()
    conn.close()
    print("数据库表初始化完成")


def _seed_hospital_departments(cursor):
    for dept_id, name, icon in HOSPITAL_DEPARTMENT_SEED:
        cursor.execute(
            '''
            INSERT OR IGNORE INTO hospital_departments (id, name, icon)
            VALUES (?, ?, ?)
            ''',
            (dept_id, name, icon),
        )


# 演示排班：排除周末；每位医生按工号固定每周约 3 个工作日（模式轮换，避免人人周一到周五全出诊）
_OUTPATIENT_WEEKDAY_PATTERNS = (
    {0, 1, 2},  # 一、二、三
    {0, 2, 4},  # 一、三、五
    {1, 2, 3},  # 二、三、四
    {1, 3, 4},  # 二、四、五
    {0, 1, 4},  # 一、二、五
)


def is_outpatient_slot_day_for_doctor(doctor_business_id, d):
    """
    是否应为该医生开放门诊号源日。
    - 周六、周日不放号；
    - 周一至周五内，按工号固定其中 3 天（与种子号源、管理端初始化、患者预约创号一致）。
    """
    if not isinstance(d, date):
        return False
    wd = d.weekday()
    if wd >= 5:
        return False
    pat = _OUTPATIENT_WEEKDAY_PATTERNS[int(doctor_business_id) % len(_OUTPATIENT_WEEKDAY_PATTERNS)]
    return wd in pat


def get_default_slot_count_for_doctor(cursor, doctor_id, fallback=40):
    """
    每个半日时段（08:00–12:00 / 14:00–18:00）的默认号源上限（与患者端「专家/普通」展示一致）：
    - 专家号：每段 20，全天两时段合计 40
    - 普通号：每段 40，全天两时段合计 80

    判定专家：科室 department_id=27（资深专家门诊），或职称为正主任医师（含「主任医师」且不含「副主任医师」）。
    """
    try:
        cursor.execute(
            'SELECT title, department_id FROM doctors WHERE doctor_id = ?',
            (doctor_id,),
        )
        row = cursor.fetchone()
        if not row:
            return fallback

        title = row['title'] or ''
        department_id = row['department_id']

        is_expert_department = department_id == 27
        is_director = ('主任医师' in title) and ('副主任医师' not in title)

        if is_expert_department or is_director:
            return 20

        return 40
    except Exception:
        return fallback


def normalize_appointment_slot_half_day_totals_for_doctor(cursor, doctor_business_id):
    """将指定医生所有号源行的 total_count 按专家/普通规则改为 20 或 40（幂等）。"""
    cursor.execute(
        'SELECT title, department_id FROM doctors WHERE doctor_id = ?',
        (int(doctor_business_id),),
    )
    row = cursor.fetchone()
    if not row:
        return
    title = (row['title'] or '')
    dept = row['department_id']
    is_expert = (dept == 27) or (
        ('主任医师' in title) and ('副主任医师' not in title)
    )
    cap = 20 if is_expert else 40
    cursor.execute(
        '''
        UPDATE appointment_slots
        SET total_count = ?,
            booked_count = MIN(booked_count, ?)
        WHERE doctor_id = ?
        ''',
        (cap, cap, int(doctor_business_id)),
    )


def normalize_appointment_slot_half_day_totals(cursor):
    """对 doctors 表中每位医生执行 normalize_appointment_slot_half_day_totals_for_doctor。"""
    cursor.execute('SELECT doctor_id FROM doctors')
    for row in cursor.fetchall():
        normalize_appointment_slot_half_day_totals_for_doctor(cursor, int(row['doctor_id']))


def seed_appointment_slots_for_doctor(cursor, doctor_business_id, days=21):
    """
    为单个医生（业务工号）插入未来号源；已存在同日同时段则忽略。
    返回新插入的时段行数（估算）。
    """
    cursor.execute('SELECT 1 FROM doctors WHERE doctor_id = ? LIMIT 1', (doctor_business_id,))
    if not cursor.fetchone():
        return 0
    time_slots = ['08:00-12:00', '14:00-18:00']
    today = datetime.now().date()
    total_per = get_default_slot_count_for_doctor(cursor, doctor_business_id, fallback=40)
    inserted = 0
    for i in range(days):
        slot_date = today + timedelta(days=i + 1)
        if not is_outpatient_slot_day_for_doctor(doctor_business_id, slot_date):
            continue
        ds = slot_date.strftime('%Y-%m-%d')
        for time_slot in time_slots:
            cursor.execute(
                '''
                INSERT OR IGNORE INTO appointment_slots (doctor_id, date, time_slot, total_count, booked_count)
                VALUES (?, ?, ?, ?, 0)
                ''',
                (doctor_business_id, ds, time_slot, total_per),
            )
            inserted += cursor.rowcount or 0
    return inserted


def reconcile_appointment_slot_booked_counts(cursor, doctor_business_id=None):
    """
    按「已确认」预约记录重算 appointment_slots.booked_count，可选限定某一医生工号。
    """
    if doctor_business_id is not None:
        bids = [int(doctor_business_id)]
    else:
        cursor.execute('SELECT DISTINCT doctor_id FROM appointment_slots')
        bids = [int(r['doctor_id']) for r in cursor.fetchall()]
    for bid in bids:
        cursor.execute(
            '''
            UPDATE appointment_slots
            SET booked_count = (
                SELECT COUNT(*) FROM appointments
                WHERE appointments.doctor_id = appointment_slots.doctor_id
                  AND appointments.date = appointment_slots.date
                  AND appointments.time_slot = appointment_slots.time_slot
                  AND appointments.status = 'confirmed'
            ),
            updated_at = CURRENT_TIMESTAMP
            WHERE doctor_id = ?
            ''',
            (bid,),
        )
        cursor.execute(
            '''
            UPDATE appointment_slots
            SET booked_count = total_count, updated_at = CURRENT_TIMESTAMP
            WHERE doctor_id = ? AND booked_count > total_count
            ''',
            (bid,),
        )
    return len(bids)


def backfill_appointment_slots_for_all_doctors(cursor, days=21):
    """为 doctors 表中每位医生补全未来号源（幂等）。"""
    cursor.execute('SELECT doctor_id FROM doctors')
    for row in cursor.fetchall():
        seed_appointment_slots_for_doctor(cursor, int(row['doctor_id']), days=days)


def _seed_slots_for_catalog(cursor, days=14):
    """为当前 doctors 表内所有医生初始化未来号源（与 get_default_slot_count_for_doctor 一致）。"""
    cursor.execute('SELECT doctor_id FROM doctors')
    for row in cursor.fetchall():
        seed_appointment_slots_for_doctor(cursor, int(row['doctor_id']), days=days)


def _ensure_doctor_catalog(cursor, conn):
    """
    写入规范医生演示数据：去重名、科室 ID 与专科一致、每科室至少一人。
    若已有预约记录则跳过整表重置（避免破坏生产数据）；仅首次或无预约库会升级。
    """
    skipped_markers = (
        CATALOG_SKIPPED_APPTS,
        '4-skipped-existing-appts',
        '3-skipped-existing-appts',
    )
    cursor.execute('SELECT value FROM app_meta WHERE key = ?', ('doctor_catalog_v',))
    ver_row = cursor.fetchone()
    cursor.execute('SELECT COUNT(*) AS c FROM appointments')
    appt_n = cursor.fetchone()['c']

    if ver_row and ver_row['value'] == DOCTOR_CATALOG_VERSION:
        return

    if ver_row and ver_row['value'] in skipped_markers:
        if appt_n > 0:
            return
        # 预约已清空，可重新应用目录

    if appt_n > 0:
        print(
            '[doctor_catalog] 检测到已有预约记录，跳过医生库自动重置；'
            '若需重建演示数据，请备份后清空 appointments 与 appointment_slots，并删除 app_meta 中 doctor_catalog_v 后重启。'
        )
        cursor.execute(
            'INSERT OR REPLACE INTO app_meta (key, value) VALUES (?, ?)',
            ('doctor_catalog_v', CATALOG_SKIPPED_APPTS),
        )
        conn.commit()
        return

    print('[doctor_catalog] 正在写入扩展演示医生目录（按子科室精确匹配，各科室至少 2 人，姓名不重复）…')
    cursor.execute('DELETE FROM appointment_slots')
    cursor.execute('DELETE FROM doctors')
    for row in FULL_DOCTOR_CATALOG:
        cursor.execute(
            '''
            INSERT INTO doctors (doctor_id, name, title, specialty, department_id, sub_department_id, specialty_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            row,
        )
    _seed_slots_for_catalog(cursor, days=14)
    cursor.execute(
        'INSERT OR REPLACE INTO app_meta (key, value) VALUES (?, ?)',
        ('doctor_catalog_v', DOCTOR_CATALOG_VERSION),
    )
    conn.commit()


def _migrate_legacy_doctor_business_ids(cursor, conn):
    """
    将 doctors / appointment_slots / appointments / users 中旧版短工号（<100000）
    按「科室 + 表内顺序」迁移为 6 位工号；已 ≥100000 的不变。
    """
    cursor.execute(
        'SELECT value FROM app_meta WHERE key = ?',
        (BUSINESS_ID_6DIGIT_MIGRATION_KEY,),
    )
    if cursor.fetchone():
        return

    cursor.execute(
        '''
        SELECT id, doctor_id, department_id, specialty_id
        FROM doctors
        ORDER BY COALESCE(department_id, 99), id
        '''
    )
    rows = cursor.fetchall()
    plan = []  # (pk, old_business_id, new_business_id)
    seq_by_dept = {}
    for r in rows:
        old = r['doctor_id']
        if old >= 100000:
            continue
        dept = r['department_id']
        if dept is None or dept < 1 or dept > 99:
            dept = 99
        seq_by_dept[dept] = seq_by_dept.get(dept, 0) + 1
        seq = seq_by_dept[dept]
        if seq > 999:
            conn.rollback()
            raise ValueError(f'科室 {dept} 医生数超过 999，无法分配 6 位工号')
        new_id = doctor_business_id(dept, seq)
        plan.append((r['id'], old, new_id))

    if not plan:
        cursor.execute(
            'INSERT OR REPLACE INTO app_meta (key, value) VALUES (?, ?)',
            (BUSINESS_ID_6DIGIT_MIGRATION_KEY, '1'),
        )
        conn.commit()
        return

    old_to_news = defaultdict(list)
    for pk, old, new in plan:
        old_to_news[old].append(new)

    # 1) doctors：先挪到负数主键行占位，避免 UNIQUE(doctor_id, specialty_id) 冲突
    for pk, old, new in plan:
        cursor.execute('UPDATE doctors SET doctor_id = ? WHERE id = ?', (-pk, pk))

    for pk, old, new in plan:
        cursor.execute('UPDATE doctors SET doctor_id = ? WHERE id = ?', (new, pk))

    # 号源/预约仅按业务工号关联：同一旧工号多专科时，统一映射到该旧号下第一个新工号
    for old, news in old_to_news.items():
        primary = news[0]
        cursor.execute(
            'UPDATE appointment_slots SET doctor_id = ? WHERE doctor_id = ?',
            (primary, old),
        )
        cursor.execute(
            'UPDATE appointments SET doctor_id = ? WHERE doctor_id = ?',
            (primary, old),
        )
        if len(news) > 1:
            print(
                f'[migrate] 警告：旧工号 {old} 对应多行医生记录，'
                f'号源/预约已关联到 {primary}，其余 {news[1:]} 无自动复制号源。'
            )

    cursor.execute(
        'UPDATE users SET doctor_business_id = ? WHERE doctor_business_id = ?',
        (DEMO_DOCTOR_BUSINESS_ID, 101),
    )
    for old, news in sorted(old_to_news.items(), key=lambda x: x[0]):
        primary = news[0]
        cursor.execute(
            'UPDATE users SET doctor_business_id = ? WHERE doctor_business_id = ?',
            (primary, old),
        )

    cursor.execute(
        'INSERT OR REPLACE INTO app_meta (key, value) VALUES (?, ?)',
        (BUSINESS_ID_6DIGIT_MIGRATION_KEY, '1'),
    )
    conn.commit()
    print(
        f'[migrate] 已将 {len(plan)} 条医生工号迁移为 6 位规则，并同步号源/预约/用户绑定。'
    )


def _seed_default_staff_users(cursor):
    """默认：管理员 admin/admin；医生 doctor/admin（绑定工号与目录中周景明一致）"""
    cursor.execute('SELECT COUNT(*) AS c FROM users WHERE role IN (?, ?)', ('admin', 'doctor'))
    row = cursor.fetchone()
    if row and row['c'] > 0:
        return
    pwd = generate_password_hash('admin')
    cursor.execute(
        '''
        INSERT INTO users (username, password_hash, role, doctor_business_id, display_name)
        VALUES (?, ?, 'admin', NULL, ?)
        ''',
        ('admin', pwd, '系统管理员'),
    )
    cursor.execute(
        '''
        INSERT INTO users (username, password_hash, role, doctor_business_id, display_name)
        VALUES (?, ?, 'doctor', ?, ?)
        ''',
        ('doctor', pwd, DEMO_DOCTOR_BUSINESS_ID, '周景明（演示）'),
    )


def _sync_demo_doctor_user_binding(cursor):
    """演示账号 doctor 始终绑定内科首位工号（与 FULL_DOCTOR_CATALOG 一致）。"""
    cursor.execute(
        '''
        UPDATE users SET doctor_business_id = ?
        WHERE username = 'doctor' AND role = 'doctor'
        ''',
        (DEMO_DOCTOR_BUSINESS_ID,),
    )

def ensure_hospital_departments_seeded():
    """若科室表被清空则重新写入种子数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) AS c FROM hospital_departments')
    if cursor.fetchone()['c'] == 0:
        _seed_hospital_departments(cursor)
        conn.commit()
    conn.close()


def init_sample_data():
    """兼容旧脚本入口；医生与号源由 init_database 内 _ensure_doctor_catalog 写入。"""
    print('提示：请使用 init_database()；医生目录会在其中自动同步。')

def force_reset_doctor_catalog_and_demo_data():
    """
    清空预约、号源与医生后重新写入标准目录（开发/演示用，会删除所有预约记录）。
    用法：python database.py --reset-doctors
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM appointment_slots')
    cursor.execute('DELETE FROM appointments')
    cursor.execute('DELETE FROM doctors')
    cursor.execute(
        'DELETE FROM app_meta WHERE key IN (?, ?)',
        ('doctor_catalog_v', BUSINESS_ID_6DIGIT_MIGRATION_KEY),
    )
    conn.commit()
    conn.close()
    init_database()
    print('已强制重置：医生目录 + 号源（预约已清空）。')


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--reset-doctors':
        force_reset_doctor_catalog_and_demo_data()
    else:
        init_database()
        init_sample_data()
