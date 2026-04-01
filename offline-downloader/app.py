import os
import json
import time
import threading
import requests
import sys
import urllib3
import libtorrent as lt
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
            # BT下载
            print("检测到BT链接，使用libtorrent下载")
            sys.stdout.flush()
            
            # 创建session
            ses = lt.session()
            ses.listen_on(6881, 6891)
            
            # 添加torrent
            params = {
                'save_path': download_dir,
                'storage_mode': lt.storage_mode_t(2),  # 存储模式
                'paused': False,
                'auto_managed': True,
                'duplicate_is_error': True
            }
            
            if url.startswith('magnet:'):
                # magnet链接
                handle = lt.add_magnet_uri(ses, url, params)
                print(f"添加magnet链接: {url}")
                sys.stdout.flush()
                # 等待元数据下载完成
                print("正在获取元数据...")
                sys.stdout.flush()
                while not handle.has_metadata():
                    time.sleep(1)
                print("元数据获取完成")
                sys.stdout.flush()
            else:
                # .torrent文件
                print(f"添加torrent文件: {url}")
                sys.stdout.flush()
                # 下载torrent文件
                torrent_file = os.path.join(download_dir, 'temp.torrent')
                with open(torrent_file, 'wb') as f:
                    response = requests.get(url, verify=False)
                    f.write(response.content)
                # 从文件加载torrent
                with open(torrent_file, 'rb') as f:
                    torrent_data = f.read()
                handle = lt.add_torrent_params(torrent_data, params)
                os.remove(torrent_file)
            
            # 开始下载
            print("开始BT下载")
            sys.stdout.flush()
            
            # 监控下载进度
            while not handle.is_seed():
                status = handle.status()
                progress = status.progress * 100
                speed = status.download_rate / 1024  # KB/s
                
                tasks[gid]['progress'] = progress
                tasks[gid]['speed'] = speed
                tasks[gid]['last_update'] = time.time()
                save_tasks()
                
                print(f"BT下载进度: {progress:.2f}%, 速度: {speed:.2f} KB/s")
                sys.stdout.flush()
                time.sleep(5)
            
            print("BT下载完成")
            sys.stdout.flush()
            tasks[gid]['status'] = 'completed'
            tasks[gid]['progress'] = 100
            save_tasks()
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
