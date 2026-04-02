import os
import json
import time
import threading
import requests
import sys
import urllib3
import subprocess
# import libtorrent as lt  # 暂时注释掉，因为安装困难
from pySmartDL import SmartDL
from flask import Flask, request, jsonify, send_from_directory

# 禁用SSL证书验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        print(f"开始下载: {url}")
        sys.stdout.flush()
        tasks[gid]['status'] = 'downloading'
        save_tasks()
        
        # 检查是否为BT链接（magnet或.torrent）
        if url.startswith('magnet:') or url.endswith('.torrent'):
            # BT下载 - 使用aria2
            print("检测到BT链接，使用aria2下载")
            sys.stdout.flush()
            
            # 使用aria2下载BT链接
            cmd = [
                'aria2c',
                url,
                '-d', download_dir,
                '--bt-enable-lpd',
                '--enable-dht',
                '--enable-peer-exchange',
                '--seed-ratio=0',
                '--summary-interval=10',
                '--follow-torrent=true',
                '--check-certificate=false'
            ]
            
            print(f"执行aria2命令: {' '.join(cmd)}")
            sys.stdout.flush()
            
            # 启动aria2进程
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            
            # 监控下载进度
            while True:
                # 检查进程是否结束
                if process.poll() is not None:
                    break
                
                # 更新进度（aria2的进度监控比较复杂，这里简化处理）
                tasks[gid]['progress'] = min(tasks[gid]['progress'] + 1, 99)
                tasks[gid]['speed'] = 0  # aria2速度监控需要更复杂的解析
                tasks[gid]['last_update'] = time.time()
                save_tasks()
                
                print(f"BT下载进度: {tasks[gid]['progress']:.2f}%")
                sys.stdout.flush()
                time.sleep(5)
            
            # 等待进程结束
            stdout, stderr = process.communicate()
            return_code = process.returncode
            
            if return_code == 0:
                print("BT下载完成")
                sys.stdout.flush()
                tasks[gid]['status'] = 'completed'
                tasks[gid]['progress'] = 100
                save_tasks()
            else:
                print(f"BT下载失败: {stderr}")
                sys.stdout.flush()
                tasks[gid]['status'] = 'failed'
                tasks[gid]['error'] = f'BT下载失败: {stderr}'
                save_tasks()
            return
        else:
            # 普通HTTP下载 - 使用pySmartDL多线程下载
            # 获取文件名
            filename = url.split('/')[-1]
            filepath = os.path.join(download_dir, filename)
            print(f"保存路径: {filepath}")
            sys.stdout.flush()
            
            # 使用pySmartDL进行多线程下载
            print(f"使用pySmartDL多线程下载: {url}")
            sys.stdout.flush()
            
            obj = SmartDL(url, dest=filepath, threads=5, progress_bar=False)
            obj.start(blocking=False)
            
            # 监控下载进度
            while not obj.isFinished():
                progress = obj.get_progress() * 100
                speed = obj.get_speed(human=False) / 1024  # KB/s
                
                tasks[gid]['progress'] = progress
                tasks[gid]['speed'] = speed
                tasks[gid]['last_update'] = time.time()
                save_tasks()
                
                print(f"HTTP下载进度: {progress:.2f}%, 速度: {speed:.2f} KB/s")
                sys.stdout.flush()
                time.sleep(1)
            
            # 检查下载是否成功
            if obj.isSuccessful():
                print(f"下载完成: {filename}")
                sys.stdout.flush()
                tasks[gid]['status'] = 'completed'
                tasks[gid]['progress'] = 100
                save_tasks()
            else:
                raise Exception(f"下载失败: {obj.get_errors()}")
    except Exception as e:
        print(f"下载失败: {str(e)}")
        sys.stdout.flush()
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

# 获取当前下载进度（从tasks中获取）
@app.route('/api/progress', methods=['GET'])
def get_current_progress():
    try:
        # 查找正在下载的任务
        current_task = None
        for gid, task in tasks.items():
            if task['status'] == 'downloading':
                current_task = task
                break
        
        if current_task:
            # 提取文件名
            url = current_task['url']
            filename = '未知文件'
            if url.startswith('magnet:'):
                filename = 'BT下载'
            else:
                filename = url.split('/')[-1]
            
            # 截断过长的文件名
            if len(filename) > 20:
                filename = filename[:17] + '...'
            
            return jsonify({
                'filename': filename,
                'progress': current_task['progress']
            })
        else:
            return jsonify({
                'filename': '无下载任务',
                'progress': 0
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 提交下载任务
@app.route('/api/download', methods=['POST'])
def add_download():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    try:
        print(f"收到下载请求: {url}")
        sys.stdout.flush()
        # 生成任务ID
        gid = str(time.time())
        print(f"生成任务ID: {gid}")
        sys.stdout.flush()
        
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
        print(f"任务已保存: {gid}")
        sys.stdout.flush()
        
        # 启动下载线程
        print(f"启动下载线程: {gid}")
        sys.stdout.flush()
        thread = threading.Thread(target=download_file, args=(gid, url))
        thread.daemon = True
        thread.start()
        print(f"下载线程已启动: {gid}")
        sys.stdout.flush()
        
        return jsonify({"gid": gid})
    except Exception as e:
        print(f"提交任务失败: {str(e)}")
        sys.stdout.flush()
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

# 删除文件
@app.route('/api/file', methods=['DELETE'])
def delete_file():
    data = request.json
    path = data.get('path', '')
    full_path = os.path.join(download_dir, path)
    
    # 安全检查，确保不会访问下载目录外的文件
    if not full_path.startswith(download_dir):
        return jsonify({"error": "Invalid path"}), 403
    
    if not os.path.exists(full_path):
        return jsonify({"error": "File not found"}), 404
    
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
            print(f"删除文件: {full_path}")
            sys.stdout.flush()
        elif os.path.isdir(full_path):
            import shutil
            shutil.rmtree(full_path)
            print(f"删除目录: {full_path}")
            sys.stdout.flush()
        return jsonify({"success": True})
    except Exception as e:
        print(f"删除失败: {str(e)}")
        sys.stdout.flush()
        return jsonify({"error": str(e)}), 500

# 提供静态文件服务
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# 根路径返回前端页面
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# 健康检查接口
@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
