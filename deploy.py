#!/usr/bin/env python3
import paramiko
import os
import sys
from scp import SCPClient


def load_deploy_config():
    """从 .deploy.env 读取部署配置"""
    config = {}
    env_path = os.path.join(os.path.dirname(__file__), ".deploy.env")

    if not os.path.exists(env_path):
        print(f"[-] 配置文件不存在: {env_path}")
        print("    请参考 .deploy.env.example 创建 .deploy.env")
        sys.exit(1)

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()

    required = ["SERVER_IP", "SERVER_USER", "SERVER_PASSWORD", "PROJECT_PATH",
                "APP_NAME", "FRONTEND_DOMAIN", "NGINX_CONFIG_PATH"]
    missing = [k for k in required if k not in config]
    if missing:
        print(f"[-] .deploy.env 缺少必要配置: {', '.join(missing)}")
        sys.exit(1)

    return config


config = load_deploy_config()
SERVER_IP = config["SERVER_IP"]
SERVER_USER = config["SERVER_USER"]
SERVER_PASSWORD = config["SERVER_PASSWORD"]
PROJECT_PATH = config["PROJECT_PATH"]
APP_NAME = config["APP_NAME"]
FRONTEND_DOMAIN = config["FRONTEND_DOMAIN"]
NGINX_CONFIG_PATH = config["NGINX_CONFIG_PATH"]
DB_PASSWORD = config["DB_PASSWORD"]

# 通配符证书 *.01rj.com 在 Let's Encrypt 中的实际存储目录名（live 下的目录）
CERT_DOMAIN = "01rj.com"


def create_ssh_client():
    print(f"[*] 连接到服务器 {SERVER_IP}...")
    print(f"    用户名: {SERVER_USER}")
    print(f"    密码: {'*' * len(SERVER_PASSWORD)}")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD,
                       timeout=30, allow_agent=False, look_for_keys=False)
        print("[+] 连接成功！")
        return client
    except paramiko.AuthenticationException as e:
        print(f"[-] 认证失败: {e}")
        print("    请检查 .deploy.env 中的用户名和密码")
        return None
    except paramiko.SSHException as e:
        print(f"[-] SSH连接失败: {e}")
        return None
    except Exception as e:
        print(f"[-] 连接错误: {e}")
        return None


def execute_command(client, command):
    print(f"[*] 执行命令: {command}")
    try:
        stdin, stdout, stderr = client.exec_command(command, timeout=120)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8', errors='replace')
        error = stderr.read().decode('utf-8', errors='replace')

        if exit_status == 0:
            print("[+] 命令执行成功")
            if output.strip():
                # safe print - replace chars that can't be encoded in console encoding
                try:
                    print(output.strip())
                except UnicodeEncodeError:
                    print(output.encode('ascii', errors='replace').decode('ascii'))
        else:
            print(f"[-] 命令执行失败 (退出码: {exit_status})")
            if error.strip():
                try:
                    print(f"    错误: {error.strip()}")
                except UnicodeEncodeError:
                    print(f"    错误: {error.encode('ascii', errors='replace').decode('ascii')}")

        return exit_status == 0, output
    except Exception as e:
        print(f"[-] 命令执行异常: {e}")
        return False, str(e)


def upload_file(client, local_path, remote_path):
    print(f"[*] 上传文件: {local_path} -> {remote_path}")

    if not os.path.exists(local_path):
        print(f"[-] 文件不存在: {local_path}")
        return False

    try:
        with SCPClient(client.get_transport()) as scp:
            scp.put(local_path, remote_path)

        file_size = os.path.getsize(local_path)
        print(f"[+] 文件上传成功！ ({file_size / 1024 / 1024:.2f} MB)")
        return True
    except Exception as e:
        print(f"[-] 文件上传失败: {e}")
        return False


def main():
    print("=" * 50)
    print("    币安合约AI监控助手 - 自动部署")
    print("=" * 50)
    print()

    try:
        client = create_ssh_client()
        if not client:
            print("\n[-] 无法连接到服务器，部署终止")
            return 1

        # 步骤1: 创建项目目录
        print("\n[步骤1/7] 创建项目目录...")
        success, _ = execute_command(client, f"mkdir -p {PROJECT_PATH} && cd {PROJECT_PATH} && pwd")

        if not success:
            print("[-] 创建项目目录失败")
            return

        # 步骤2: 安装必要软件
        print("\n[步骤2/7] 安装必要软件...")
        print("    这可能需要几分钟时间...")

        print("    更新系统...")
        execute_command(client, "sudo apt update -qq")

        print("    安装Python和pip...")
        execute_command(client, "sudo apt install -y python3 python3-pip python3-venv -qq")

        print("    安装Node.js和npm...")
        execute_command(client, "curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt install -y nodejs -qq")

        print("    安装PM2...")
        execute_command(client, "sudo npm install -g pm2")

        print("    安装unzip...")
        execute_command(client, "sudo apt install -y unzip -qq")

        # 步骤3: 压缩后端文件
        print("\n[步骤3/7] 压缩后端文件...")
        import zipfile

        if os.path.exists("backend.zip"):
            os.remove("backend.zip")

        print("    正在压缩backend文件夹...")
        EXCLUDE_DIRS = {".git", "venv", ".venv", "__pycache__", "instance", "logs"}
        file_count = 0
        with zipfile.ZipFile("backend.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk("backend"):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, "backend")
                    zipf.write(file_path, arcname)
                    file_count += 1

        print(f"[+] 压缩完成！({file_count} 个文件)")

        # 步骤4: 上传后端文件
        print("\n[步骤4/9] 上传后端文件...")
        success = upload_file(client, "backend.zip", f"{PROJECT_PATH}/backend.zip")

        if not success:
            print("[-] 上传失败，部署终止")
            return

        # 步骤5: 解压后端文件
        print("\n[步骤5/9] 解压后端文件...")
        success, output = execute_command(client, f"cd {PROJECT_PATH} && mkdir -p backend && python3 -c \"import zipfile; zipfile.ZipFile('backend.zip').extractall('backend/')\" && ls -la backend/")

        if not success:
            print("[-] 解压失败")
            return

        # 步骤5.5: 更新.env文件中的数据库配置
        print("\n[步骤5.5/9] 更新数据库配置...")
        print("    更新数据库主机为127.0.0.1...")
        execute_command(client, f"cd {PROJECT_PATH}/backend && sed -i 's/^DATABASE_HOST=.*/DATABASE_HOST=127.0.0.1/' .env 2>/dev/null || echo 'DATABASE_HOST=127.0.0.1' >> .env")

        print("    更新数据库用户为root...")
        execute_command(client, f"cd {PROJECT_PATH}/backend && sed -i 's/^DATABASE_USER=.*/DATABASE_USER=root/' .env 2>/dev/null || echo 'DATABASE_USER=root' >> .env")

        print("    更新数据库密码...")
        execute_command(client, f"cd {PROJECT_PATH}/backend && sed -i 's/^DATABASE_PASSWORD=.*/DATABASE_PASSWORD={DB_PASSWORD}/' .env 2>/dev/null || echo 'DATABASE_PASSWORD={DB_PASSWORD}' >> .env")

        print("    验证.env文件...")
        success, output = execute_command(client, f"cd {PROJECT_PATH}/backend && cat .env | grep DATABASE")
        if success:
            print("[+] 数据库配置更新成功")
        else:
            print("[-] 数据库配置更新失败")

        # 步骤6: 安装Python依赖
        print("\n[步骤6/9] 安装Python依赖...")
        print("    创建虚拟环境...")
        success, output = execute_command(client, f"cd {PROJECT_PATH}/backend && python3 -m venv venv")

        if not success:
            print("[-] 创建虚拟环境失败")
            print("    错误输出:", output)
            return

        print("    正在安装依赖包，请稍候...")
        success, output = execute_command(client, f"cd {PROJECT_PATH}/backend && ./venv/bin/pip install -r requirements.txt --quiet --no-cache-dir")

        if not success:
            print("[-] Python依赖安装失败")
            print("    错误输出:", output)
            return

        # 步骤7: 压缩前端文件
        print("\n[步骤7/9] 压缩前端文件...")
        if os.path.exists("frontend.zip"):
            os.remove("frontend.zip")

        print("    正在压缩frontend/dist文件夹...")
        file_count = 0
        with zipfile.ZipFile("frontend.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk("frontend/dist"):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, "frontend/dist")
                    zipf.write(file_path, arcname)
                    file_count += 1

        print(f"[+] 压缩完成！({file_count} 个文件)")

        # 步骤8: 上传前端文件
        print("\n[步骤8/9] 上传前端文件...")
        success = upload_file(client, "frontend.zip", f"{PROJECT_PATH}/frontend.zip")

        if not success:
            print("[-] 上传失败，部署终止")
            return

        print("    解压前端文件...")
        success, output = execute_command(client, f"cd {PROJECT_PATH} && mkdir -p frontend && python3 -c \"import zipfile; zipfile.ZipFile('frontend.zip').extractall('frontend/')\" && ls -la frontend/")

        if not success:
            print("[-] 解压失败")
            return

        print("    设置前端文件权限...")
        execute_command(client, f"sudo chmod -R 755 {PROJECT_PATH}/frontend")
        execute_command(client, f"sudo chown -R ubuntu:ubuntu {PROJECT_PATH}/frontend")
        execute_command(client, f"sudo find {PROJECT_PATH}/frontend -type d -exec chmod 755 {{}} \\;")
        execute_command(client, f"sudo find {PROJECT_PATH}/frontend -type f -exec chmod 644 {{}} \\;")
        print("[+] 权限设置完成")

        # 步骤9: 启动服务
        print("\n[步骤9/9] 启动服务...")
        print("    停止旧服务...")
        execute_command(client, f"pm2 stop {APP_NAME} 2>/dev/null; pm2 delete {APP_NAME} 2>/dev/null")
        execute_command(client, f"pm2 stop {APP_NAME}-frontend 2>/dev/null; pm2 delete {APP_NAME}-frontend 2>/dev/null")

        print("    启动后端服务...")
        success, _ = execute_command(client, f"cd {PROJECT_PATH}/backend && pm2 start app.py --name {APP_NAME} --cwd {PROJECT_PATH}/backend --interpreter {PROJECT_PATH}/backend/venv/bin/python")

        if not success:
            print("[-] PM2启动失败")
            return

        print("    配置防火墙...")
        execute_command(client, "sudo ufw allow 3008/tcp 2>/dev/null || echo 'ufw not available, skip'")

        print("    配置Nginx...")

        print("    清理旧的Nginx配置...")
        execute_command(client, "sudo rm -f /etc/nginx/sites-enabled/default")
        execute_command(client, f"sudo rm -f /etc/nginx/sites-available/{FRONTEND_DOMAIN}.conf")
        execute_command(client, f"sudo rm -f /etc/nginx/sites-enabled/{FRONTEND_DOMAIN}.conf")

        nginx_config = f"""# HTTPS (443)
server {{
    listen 443 ssl http2;
    server_name {FRONTEND_DOMAIN};

    ssl_certificate /etc/letsencrypt/live/{CERT_DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{CERT_DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {{
        root {PROJECT_PATH}/frontend;
        try_files $uri $uri/ /index.html;
        index index.html;
    }}

    location /api/ {{
        proxy_pass http://localhost:3007/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    location /ws {{
        proxy_pass http://localhost:3007/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}

# HTTPS (3008)
server {{
    listen 3008 ssl http2;
    server_name {FRONTEND_DOMAIN};

    ssl_certificate /etc/letsencrypt/live/{CERT_DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{CERT_DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {{
        root {PROJECT_PATH}/frontend;
        try_files $uri $uri/ /index.html;
        index index.html;
    }}

    location /api/ {{
        proxy_pass http://localhost:3007/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    location /ws {{
        proxy_pass http://localhost:3007/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""

        success, output = execute_command(client, f"echo '{nginx_config}' | sudo tee {NGINX_CONFIG_PATH}")

        if not success:
            print("[-] Nginx配置文件创建失败")
            return

        print("    启用Nginx配置...")
        success, output = execute_command(client, f"sudo ln -sf {NGINX_CONFIG_PATH} /etc/nginx/sites-enabled/")

        if not success:
            print("[-] Nginx配置启用失败")
            return

        print("    测试Nginx配置...")
        success, output = execute_command(client, "sudo nginx -t")

        if not success:
            print("[-] Nginx配置测试失败")
            print("    错误输出:", output)
            return

        print("    重启Nginx服务...")
        success, output = execute_command(client, "sudo systemctl restart nginx")

        if not success:
            print("[-] Nginx重启失败")
            return

        print("\n[*] 等待服务启动...")
        import time
        time.sleep(5)

        print("\n[最后步骤] 检查服务状态...")
        execute_command(client, "pm2 list")

        client.close()

        print("\n" + "=" * 50)
        print("    部署完成！")
        print("=" * 50)
        print()
        print(f"后端服务: PM2管理 ({APP_NAME})")
        print(f"前端服务: Nginx (HTTPS)")
        print(f"项目路径: {PROJECT_PATH}")
        print()
        print("访问地址:")
        print(f"- 前端页面 (443): https://{FRONTEND_DOMAIN}")
        print(f"- 前端页面 (3008): https://{FRONTEND_DOMAIN}:3008")
        print(f"- 后端API: https://{FRONTEND_DOMAIN}/api")
        print(f"- 健康检查: https://{FRONTEND_DOMAIN}/health")
        print(f"- API文档: https://{FRONTEND_DOMAIN}/docs")
        print()
        print("=" * 50)
        print()
        print("PM2管理命令:")
        print(f"1. 查看状态: ssh {SERVER_USER}@{SERVER_IP} 'pm2 list'")
        print(f"2. 查看后端日志: ssh {SERVER_USER}@{SERVER_IP} 'pm2 logs {APP_NAME}'")
        print(f"3. 重启后端: ssh {SERVER_USER}@{SERVER_IP} 'pm2 restart {APP_NAME}'")
        print(f"4. 停止服务: ssh {SERVER_USER}@{SERVER_IP} 'pm2 stop {APP_NAME}'")
        print(f"5. 开机自启: ssh {SERVER_USER}@{SERVER_IP} 'pm2 startup && pm2 save'")
        print()
        print("Nginx管理命令:")
        print(f"1. 查看Nginx状态: ssh {SERVER_USER}@{SERVER_IP} 'sudo systemctl status nginx'")
        print(f"2. 查看Nginx日志: ssh {SERVER_USER}@{SERVER_IP} 'sudo tail -f /var/log/nginx/error.log'")
        print(f"3. 重启Nginx: ssh {SERVER_USER}@{SERVER_IP} 'sudo systemctl restart nginx'")
        print(f"4. 测试配置: ssh {SERVER_USER}@{SERVER_IP} 'sudo nginx -t'")
        print()

    except Exception as e:
        print(f"\n[-] 部署失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
