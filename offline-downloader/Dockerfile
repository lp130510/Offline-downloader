# 使用提供的Nginx镜像
FROM crpi-vd2np7sloa8wv5h3.cn-qingdao.personal.cr.aliyuncs.com/rhzz/nginx:latest

# 完全清除所有官方源配置，只使用清华源
RUN rm -rf /etc/apt/sources.list.d/* && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bullseye main contrib non-free" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bullseye-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bullseye-backports main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bullseye-security main contrib non-free" >> /etc/apt/sources.list

# 安装Python和pip
RUN apt-get update && apt-get install -y python3 python3-pip python3-dev build-essential

# 安装aria2
RUN apt-get install -y aria2

# 创建应用目录
RUN mkdir -p /app

# 复制应用文件
COPY . /app

# 安装Python依赖
RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn -r /app/requirements.txt

# 复制Nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 创建下载目录
RUN mkdir -p /download

# 启动脚本
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 暴露端口
EXPOSE 8021

# 启动服务
CMD ["/start.sh"]
