# 医疗系统

基于 Vue 3 + Flask + SQLite 的医疗业务演示系统，支持 Web 与 Android（Capacitor）。

## 核心功能

- **AI 问诊**
  - 文本问诊与图片问诊（阿里云百炼 OpenAI 兼容接口）
  - 对话历史保存、切换、删除
  - 人群+身体部位智能分诊，支持一键跳转挂号
- **在线挂号**
  - 科室 -> 子科室 -> 专科 -> 医生/时段 -> 就诊人 -> 预约
  - 实时号源展示与扣减
- **挂号记录**
  - 查询、筛选、取消预约、删除已取消记录
- **就诊人管理**
  - 新增、编辑、删除，就诊时复用
- **院内导航**
  - 示例楼层导览与路径提示

## 技术栈

- 前端：`Vue 3`、`Vue Router`、`Vite`、`Axios`
- 后端：`Flask`、`Flask-CORS`
- 数据：`SQLite`（`backend/medical_system.db`）
- AI：`openai` SDK + DashScope 兼容端点
- 移动端：`Capacitor 8`（Android）

## 项目结构

```text
Medical system/
├─ src/                     # 前端源码
│  ├─ views/                # 页面组件
│  └─ router/               # 路由配置
├─ backend/                 # Flask后端与数据库
│  ├─ app.py
│  ├─ database.py
│  ├─ config.py
│  └─ medical_system.db
├─ android/                 # Capacitor Android 工程
├─ public/                  # 静态资源（含 triage 人体图）
└─ scripts/                 # 移动端辅助脚本
```

## 本地运行

### 1) 安装前端依赖

```bash
npm install
```

### 2) 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 3) 启动后端

```bash
cd backend
python app.py
```

### 4) 启动前端（新终端）

```bash
npm run dev
```

## 移动端（Android）

1. 复制并配置 `.env.mobile`：

```bash
copy .env.mobile.example .env.mobile
```

2. 执行构建与同步：

```bash
npm run mobile:build
```

3. 打开 Android 工程：

```bash
npm run mobile:android
```

## 主要 API

- `POST /api/ai-consultation`
- `GET /api/appointment-slots`
- `POST /api/appointment`
- `GET /api/appointments`
- `POST /api/appointments/<appointment_id>/cancel`
- `DELETE /api/appointments/<appointment_id>`
- `GET/POST/PUT/DELETE /api/patients`
- `GET/POST/DELETE /api/consultation-history`

## 配置与安全

- AI 密钥配置见 `backend/config.py`（推荐使用环境变量）。
- 请勿提交真实密钥与敏感数据到版本库。
- 当前用于演示，生产环境请补充鉴权、审计、加密与脱敏。
