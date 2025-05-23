# 小火机器人

一个基于Python和FastAPI构建的飞书机器人，可以：
1. 与用户交互询问需要加入的群组类型
2. 要求用户发送二维码进行验证
3. 调用API验证用户权限
4. 将通过验证的用户添加到相应群组

## 环境配置

1. 克隆此仓库
2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```
3. 从`.env.example`复制创建`.env`文件并配置必要的环境变量：
   ```
   cp .env.example .env
   # 然后编辑.env文件设置必要的环境变量
   ```
4. 在`config/config.py`中配置群组ID列表
5. 启动服务：
   ```
   uvicorn app.main:app --reload
   ```

## 必要的环境变量

以下环境变量是必须配置的：

```
# 飞书机器人凭证
FEISHU_APP_ID=your_app_id_here
FEISHU_APP_SECRET=your_app_secret_here

# API验证配置
API_ENDPOINT=your_api_endpoint_here
API_TOKEN=your_api_token_here
EVENT_ID=your_event_id_here
```

其他可选环境变量见`.env.example`文件。

## 项目结构

- `app/`: 主应用代码
  - `main.py`: FastAPI应用程序入口点
  - `bot/`: 机器人相关功能
    - `handlers.py`: 事件处理逻辑
    - `messages.py`: 消息发送工具
    - `cards.py`: 交互卡片生成
  - `qrcode/`: 二维码处理
    - `parser.py`: 二维码解析工具
  - `verification/`: 验证相关功能
    - `api_client.py`: 调用外部API验证用户权限
  - `group/`: 群组管理
    - `manager.py`: 群组操作工具
- `config/`: 配置文件
  - `config.py`: 应用程序配置
- `utils/`: 工具类
  - `authentication.py`: 飞书API认证
  - `redis_client.py`: Redis客户端和状态管理
- `.env.example`: 环境变量模板
- `.gitignore`: Git忽略文件
- `requirements.txt`: 项目依赖

## 功能流程

1. 用户添加小火机器人
2. 小火询问用户要加入哪类群组（选手群或评委群）
3. 用户选择群组类型
4. 小火要求用户发送二维码
5. 小火解析二维码并调用API验证用户权限
6. 验证通过后，将用户添加到相应群组

## Redis状态管理

系统使用Redis管理用户交互状态，包括：

- 用户当前状态跟踪（初始状态、等待选择群组、等待二维码等）
- 验证结果缓存
- 用户偏好设置
