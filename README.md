# 私有离线下载工具

一个功能强大的私有离线下载工具，支持HTTP/HTTPS多线程下载和BT下载，提供简洁美观的Web界面，支持Docker容器化部署。

## 功能特性

### 核心功能
- **多协议支持**：支持HTTP/HTTPS和BT下载（magnet链接、.torrent文件）
- **多线程下载**：HTTP下载使用pySmartDL库实现多线程下载，提升下载速度
- **BT下载**：集成aria2，支持BT协议下载
- **实时进度显示**：前端实时显示当前下载进度、文件名和下载百分比
- **文件管理**：支持文件浏览、下载和删除操作
- **任务管理**：支持查看下载任务列表和取消任务

### 界面特性
- **现代化UI**：使用Bootstrap 5构建，界面简洁美观
- **响应式设计**：支持PC和移动设备访问
- **实时更新**：进度自动刷新，无需手动刷新页面
- **文件名优化**：长文件名自动截断，界面更简洁

### 技术特性
- **容器化部署**：使用Docker Compose一键部署
- **双容器架构**：Nginx提供静态文件服务，Python运行后端服务
- **健康检查**：容器自动健康检查，确保服务稳定
- **国内源优化**：使用清华源，国内环境下载更快

## 技术栈

### 后端
- **Python 3.12**：主要编程语言
- **Flask 2.2.5**：Web框架
- **pySmartDL**：多线程HTTP下载库
- **aria2**：BT下载引擎
- **requests**：HTTP请求库

### 前端
- **HTML5 + CSS3**：页面结构和样式
- **Bootstrap 5**：UI框架
- **原生JavaScript**：交互逻辑

### 部署
- **Docker**：容器化部署
- **Docker Compose**：容器编排
- **Nginx**：静态文件服务和反向代理

## 项目结构

```
offline-downloader/
├── app.py                 # Flask后端主程序
├── requirements.txt       # Python依赖
├── docker-compose.yml     # Docker Compose配置
├── Dockerfile.python      # Python容器Dockerfile
├── Dockerfile            # Nginx容器Dockerfile
├── nginx.conf            # Nginx配置文件
├── start-python.sh       # Python容器启动脚本
├── start.sh              # 启动脚本
├── static/
│   └── index.html        # 前端页面
└── README.md             # 项目文档
```

## 快速开始

### 前置要求
- Docker
- Docker Compose
- Git（可选）

### 安装部署

1. **克隆项目**（如果使用Git）
```bash
git clone <repository-url>
cd offline-downloader
```

2. **启动服务**
```bash
docker-compose up -d --build
```

3. **访问服务**
打开浏览器访问：http://localhost:8021

### 停止服务
```bash
docker-compose down
```

### 重启服务
```bash
docker-compose restart
```

## 使用方法

### 1. 下载文件

#### HTTP/HTTPS下载
1. 在"下载任务管理"区域，输入框中粘贴下载链接
2. 点击"开始下载"按钮
3. 在"当前下载进度"区域查看实时下载进度

#### BT下载
1. 在"下载任务管理"区域，输入框中粘贴magnet链接或.torrent文件链接
2. 点击"开始下载"按钮
3. 系统会自动识别BT链接并使用aria2下载

### 2. 查看下载进度
- "当前下载进度"区域会实时显示：
  - 当前下载的文件名
  - 下载进度条
  - 下载百分比
  - 更新时间
- 页面每3秒自动刷新进度

### 3. 管理下载任务
- 在"下载任务管理"区域查看任务列表
- 点击"取消"按钮可以取消正在进行的下载任务
- 任务列表每10秒自动刷新

### 4. 文件管理
- 在"文件浏览器"区域查看已下载的文件
- 点击文件名可以下载文件
- 点击"删除"按钮可以删除文件或目录
- 支持按名称、大小、修改时间排序

## API文档

### 文件管理API

#### 获取文件列表
```
GET /api/files?path=<path>
```
**参数**：
- `path`：文件路径（可选，默认为根目录）

**返回示例**：
```json
[
  {
    "name": "example.txt",
    "type": "file",
    "size": 1024,
    "mtime": 1617181723
  }
]
```

#### 删除文件
```
DELETE /api/file
```
**请求体**：
```json
{
  "path": "example.txt"
}
```

**返回示例**：
```json
{
  "success": true
}
```

### 任务管理API

#### 提交下载任务
```
POST /api/download
```
**请求体**：
```json
{
  "url": "https://example.com/file.zip"
}
```

**返回示例**：
```json
{
  "gid": "1617181723.123456"
}
```

#### 获取任务列表
```
GET /api/tasks
```

**返回示例**：
```json
[
  {
    "gid": "1617181723.123456",
    "url": "https://example.com/file.zip",
    "status": "downloading",
    "progress": 45.5,
    "speed": 1024,
    "created_at": 1617181723,
    "last_update": 1617181725
  }
]
```

#### 取消任务
```
DELETE /api/task/<gid>
```

**返回示例**：
```json
{
  "success": true
}
```

### 进度查询API

#### 获取当前下载进度
```
GET /api/progress
```

**返回示例**：
```json
{
  "filename": "example.zip",
  "progress": 45.5,
  "time": "16:30:45"
}
```

### 健康检查API

#### 健康检查
```
GET /health
```

**返回示例**：
```json
{
  "status": "healthy"
}
```

## 配置说明

### 端口配置
默认使用8021端口，可以在`docker-compose.yml`中修改：
```yaml
services:
  nginx:
    ports:
      - "8021:8021"  # 修改为你想要的端口
```

### 下载目录配置
默认下载目录为`/home/liping/liping123/yun测试云盘/download`，可以在`docker-compose.yml`中修改：
```yaml
services:
  python:
    volumes:
      - /your/download/path:/download  # 修改为你想要的路径
```

### Nginx配置
Nginx配置文件为`nginx.conf`，可以根据需要修改：
- 静态文件服务配置
- 反向代理配置
- 日志配置

### Python配置
Python后端配置在`app.py`中：
- `download_dir`：下载目录
- `tasks_file`：任务状态文件

## 常见问题

### 1. 下载速度慢怎么办？
- HTTP下载：pySmartDL会自动使用多线程下载
- BT下载：确保DHT和PEX功能正常，aria2已启用这些功能
- 检查网络连接和带宽

### 2. BT下载无法连接？
- 检查网络是否支持BT协议
- 确保防火墙没有阻止BT连接
- 尝试使用不同的tracker

### 3. 容器启动失败？
- 检查端口是否被占用
- 检查Docker和Docker Compose版本
- 查看容器日志：`docker-compose logs`

### 4. 文件删除失败？
- 检查文件权限
- 确保文件没有被占用
- 查看Python容器日志

### 5. 前端无法访问后端API？
- 检查Nginx配置是否正确
- 确保Python容器正常运行
- 检查网络连接

### 6. 如何查看日志？
```bash
# 查看所有容器日志
docker-compose logs

# 查看Python容器日志
docker-compose logs python

# 查看Nginx容器日志
docker-compose logs nginx

# 实时查看日志
docker-compose logs -f
```

## 安全建议

1. **访问控制**：建议在生产环境中添加身份认证
2. **HTTPS**：建议配置HTTPS证书
3. **防火墙**：限制访问端口，只开放必要端口
4. **定期备份**：定期备份下载目录和配置文件
5. **日志监控**：定期检查日志，发现异常及时处理

## 性能优化

1. **多线程下载**：HTTP下载默认使用5个线程
2. **BT优化**：aria2已启用DHT和PEX，提升BT下载速度
3. **Nginx优化**：配置了静态文件缓存
4. **容器资源**：可以根据需要调整容器资源限制

## 更新日志

### v1.0.0 (2026-04-01)
- 初始版本发布
- 支持HTTP/HTTPS和BT下载
- 实现文件管理和任务管理
- 添加实时进度显示
- 支持文件删除功能
- 完成Docker容器化部署

## 许可证

本项目仅供学习和研究使用，请勿用于商业用途。

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题或建议，请提交Issue。

---

**注意**：本项目仅供学习和研究使用，请遵守相关法律法规，不要下载和传播侵权内容。
