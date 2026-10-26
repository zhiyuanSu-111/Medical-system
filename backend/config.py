"""
配置文件
用于管理API密钥和其他配置项
"""
import os

# 阿里云百炼（DashScope）API密钥
# 优先从环境变量读取，如果没有则使用默认值
# 注意：生产环境应该使用环境变量，不要将API密钥硬编码在代码中
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', 'sk-27d56fb57b1c46039654b0cee38e0887')

# 阿里云百炼API配置
DASHSCOPE_BASE_URL = os.getenv('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')

# 文本对话模型配置（阿里云百炼模型）
# 可选模型：qwen-plus, qwen-turbo, qwen-max, qwen3-max 等
# 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
DASHSCOPE_MODEL = os.getenv('DASHSCOPE_MODEL', 'qwen3-max')

# 图像多模态模型（例如 qwen3-vl-plus），用于图片问诊
DASHSCOPE_VISION_MODEL = os.getenv('DASHSCOPE_VISION_MODEL', 'qwen3-vl-plus')
DASHSCOPE_MAX_TOKENS = int(os.getenv('DASHSCOPE_MAX_TOKENS', '500'))
DASHSCOPE_TEMPERATURE = float(os.getenv('DASHSCOPE_TEMPERATURE', '0.7'))

# 验证API密钥格式
def validate_api_key(api_key):
    """验证API密钥格式"""
    if not api_key:
        return False, "API密钥不能为空"
    if not api_key.startswith('sk-'):
        return False, "API密钥应以'sk-'开头"
    if len(api_key) < 20:
        return False, f"API密钥长度不足（当前长度: {len(api_key)}，至少需要20个字符）"
    # 接受不同长度的API密钥（不同服务可能有不同格式）
    return True, "API密钥格式正确"

# 验证当前API密钥
is_valid, message = validate_api_key(DASHSCOPE_API_KEY)
if not is_valid:
    print(f"警告: {message}")
    print(f"当前API密钥长度: {len(DASHSCOPE_API_KEY)}")
    print("请检查API密钥是否正确配置")
else:
    print(f"API密钥验证通过，使用阿里云百炼（DashScope）服务")
    print(f"文本模型: {DASHSCOPE_MODEL}")
    print(f"图像模型: {DASHSCOPE_VISION_MODEL}")
    print(f"API端点: {DASHSCOPE_BASE_URL}")
