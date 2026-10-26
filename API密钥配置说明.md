# API 密钥配置说明（DashScope）

当前后端默认使用阿里云百炼（DashScope）的 OpenAI 兼容接口，核心配置位于 `backend/config.py`。

## 1. 当前使用的配置项

- `DASHSCOPE_API_KEY`
- `DASHSCOPE_BASE_URL`
- `DASHSCOPE_MODEL`
- `DASHSCOPE_VISION_MODEL`
- `DASHSCOPE_MAX_TOKENS`
- `DASHSCOPE_TEMPERATURE`

## 2. 推荐配置方式（环境变量）

在系统环境变量中设置：

```bash
DASHSCOPE_API_KEY=你的密钥
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen3-max
DASHSCOPE_VISION_MODEL=qwen3-vl-plus
```

说明：当前后端校验规则只要求密钥以 `sk-` 开头且长度不少于 20。

## 3. 验证方式

可在 `backend` 目录执行：

```bash
python -c "from config import validate_api_key, DASHSCOPE_API_KEY; print(validate_api_key(DASHSCOPE_API_KEY))"
```

启动后端时也会打印密钥校验状态与模型信息。

## 4. 常见错误

- **401 / unauthorized / invalid_api_key**
  - 密钥错误、失效，或服务权限不足
- **quota / insufficient_quota**
  - 账户额度不足
- **connection / timeout**
  - 网络连通性问题

## 5. 安全建议

- 不要把真实密钥提交到仓库；
- 生产环境请使用环境变量或密钥管理服务；
- 建议定期轮换密钥。
