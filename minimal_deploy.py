#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小部署：只更新 backend/routes.py 和 frontend/dist，重启后端。"""
import os
import sys
import time
import zipfile
import paramiko
from scp import SCPClient

BASE = r"C:\Users\Administrator\Desktop\山寨策略"
SERVER_IP = "43.129.71.90"
SERVER_USER = "ubuntu"
SERVER_PASSWORD = "iDuocepQm8qAmMjharI5sD0f"
PROJECT_PATH = "/home/ubuntu/server/crypto_monitor"
APP_NAME = "crypto_monitor"


def p(s):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode("ascii", "replace").decode("ascii"))


def run(client, cmd):
    p(f"[*] {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=120)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    if out.strip():
        p(out.strip())
    if code != 0 and err.strip():
        p(f"[-] stderr: {err.strip()}")
    return code, out


def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD,
                   timeout=30, allow_agent=False, look_for_keys=False)
    p("[+] 已连接服务器")

    scp = SCPClient(client.get_transport())

    # 1) 后端 routes.py
    local_routes = os.path.join(BASE, "backend", "routes.py")
    p("[1/4] 上传 backend/routes.py")
    scp.put(local_routes, f"{PROJECT_PATH}/backend/routes.py")
    p("[+] routes.py 已上传")

    # 2) 前端 dist 打包上传
    p("[2/4] 打包 frontend/dist")
    dist_dir = os.path.join(BASE, "frontend", "dist")
    zip_path = os.path.join(BASE, "frontend_dist.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    n = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(dist_dir):
            for f in files:
                fp = os.path.join(root, f)
                arc = os.path.relpath(fp, dist_dir)
                zf.write(fp, arc)
                n += 1
    p(f"[+] 打包完成 ({n} 个文件)")

    p("[3/4] 上传并解压前端")
    scp.put(zip_path, "/tmp/frontend_dist.zip")
    run(client, f"cd {PROJECT_PATH}/frontend && rm -rf assets && rm -f index.html && "
                "python3 -c \"import zipfile; zipfile.ZipFile('/tmp/frontend_dist.zip').extractall('.')\" && "
                "sudo chown -R ubuntu:ubuntu . && ls -la")

    # 3) 重启后端
    p("[4/4] 重启后端")
    run(client, f"pm2 restart {APP_NAME}")

    p("[*] 等待 6 秒...")
    time.sleep(6)

    p("[*] 健康检查")
    code, out = run(client, "curl -s http://localhost:3007/api/health")
    p("[*] 验证 sort_by 参数")
    run(client, "curl -s 'http://localhost:3007/api/coins/timeframe-changes?limit=3&volume_threshold=5000000&sort_by=volume_24h' | python3 -c \"import sys,json; d=json.load(sys.stdin); print([ (c['symbol'], round(c['volume_24h']/1e6,1)) for c in d.get('coins',[])])\"")
    run(client, "pm2 list")

    scp.close()
    client.close()
    p("\n[+] 部署完成")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[-] 失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
