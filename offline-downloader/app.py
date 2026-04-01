import os
import json
import time
import threading
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# 配置
download_dir = '/download'
tasks_file = 'tasks.json'

# 确保下载目录存在
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# 任务状态存储
tasks = {}

# 加载任务状态
def load_tasks():
    global tasks
    if os.path.exists(tasks_file):
        try:
            with open(tasks_file, 'r') as f:
                tasks = json.load(f)
        except:
            tasks = {}

# 保存任务状态
def save_tasks():
    with open(tasks_file, 'w') as f:
        json.dump(tasks, f)

# 下载函数
def download_file(gid, url):
    try:
        tasks[gid]['status'] = 'downloading'
        save_tasks()
        
        # 获取文件名
        filename = url.split('/')[-1]
        filepath = os.path.join(download_dir, filename)
        
        # 开始下载
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # 更新进度
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        tasks[gid]['progress'] = progress
                        # 简单计算速度
                        current_time = time.time()
                        time_elapsed = current_time - tasks[gid]['last_update']
                        if time_elapsed > 0:
                            tasks[gid]['speed'] = (len(chunk) / time_elapsed) * 8
                            tasks[gid]['last_update'] = current_time
                        save_tasks()
        
        tasks[gid]['status'] = 'completed'
        tasks[gid]['progress'] = 100
        save_tasks()
    except Exception as e:
        tasks[gid]['status'] = 'failed'
        tasks[gid]['error'] = str(e)
        save_tasks()

# 初始化加载任务
load_tasks()

# 获取文件列表
@app.route('/api/files', methods=['GET'])
def get_files():
    path = request.args.get('path', '')
    full_path = os.path.join(download_dir, path)
    
    # 安全检查，确保不会访问下载目录外的文件
    if not full_path.startswith(download_dir):
        return jsonify({"error": "Invalid path"}), 403
    
    if not os.path.exists(full_path):
        return jsonify({"error": "Path not found"}), 404
    
    files = []
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        if os.path.isdir(item_path):
            files.append({
                "name": item,
                "type": "directory",
                "size": 0,
                "mtime": os.path.getmtime(item_path)
            })
        else:
            files.append({
                "name": item,
                "type": "file",
                "size": os.path.getsize(item_path),
                "mtime": os.path.getmtime(item_path)
            })
    
    return jsonify(files)

# 获取任务列表
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    # 清理已完成或失败的任务
    for gid in list(tasks.keys()):
        if tasks[gid]['status'] in ['completed', 'failed']:
            del tasks[gid]
    
    save_tasks()
    return jsonify(list(tasks.values()))

# 提交下载任务
@app.route('/api/download', methods=['POST'])
def add_download():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    try:
        # 生成任务ID
        gid = str(time.time())
        
        # 保存任务信息
        tasks[gid] = {
            "gid": gid,
            "url": url,
            "status": "pending",
            "progress": 0,
            "speed": 0,
            "created_at": time.time(),
            "last_update": time.time()
        }
        
        save_tasks()
        
        # 启动下载线程
        thread = threading.Thread(target=download_file, args=(gid, url))
        thread.daemon = True
        thread.start()
        
        return jsonify({"gid": gid})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 取消下载任务
@app.route('/api/task/<gid>', methods=['DELETE'])
def remove_task(gid):
    if gid in tasks:
        try:
            del tasks[gid]
            save_tasks()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Task not found"}), 404

# 提供静态文件服务
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# 根路径返回前端页面
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
