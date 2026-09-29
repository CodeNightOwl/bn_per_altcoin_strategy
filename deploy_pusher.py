#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""部署信号推送：上传后端文件 + 重启，验证 pusher 启动。"""
import os
import time
import paramiko
from scp import SCPClient

BASE = r"C:\Users\Administrator\Desktop\山寨策略"
SERVER_IP = "43.129.71.90"
SERVER_USER = "ubuntu"
SERVER_PASSWORD = "iDuocepQm8qAmMjharI5sD0f"
PROJECT_PATH = "/home/ubuntu/server/crypto_monitor"
APP_NAME = "crypto_monitor"

FILES = [
    "config.py",
    "app.py",
    "push_service.py",
    "requirements.txt",
    ".env",
]


def p(s):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode("ascii", "replace").decode("ascii"))


def run(client, cmd, timeout=120):
    p(f"[*] {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
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

    for f in FILES:
        local = os.path.join(BASE, "backend", f)
        remote = f"{PROJECT_PATH}/backend/{f}"
        p(f"[*] 上传 {f}")
        scp.put(local, remote)

    p("[*] 重启后端")
    run(client, f"pm2 restart {APP_NAME}")
    p("[*] 等待 10 秒...")
    time.sleep(10)

    p("[*] 健康检查")
    run(client, "curl -s http://localhost:3007/api/health")

    p("[*] 最近日志 (检查 SignalPusher)")
    run(client, f"pm2 logs {APP_NAME} --lines 40 --nostream")

    scp.close()
    client.close()
    p("\n[+] 部署完成")
    return 0


if __name__ == "__main__":
    try:
        import sys
        sys.exit(main())
    except Exception as e:
        print(f"[-] 失败: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
