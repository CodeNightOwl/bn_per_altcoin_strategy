#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, zipfile, paramiko
from scp import SCPClient

BASE = r"C:\Users\Administrator\Desktop\山寨策略"
SERVER_IP = "43.129.71.90"
SERVER_USER = "ubuntu"
SERVER_PASSWORD = "iDuocepQm8qAmMjharI5sD0f"
PROJECT_PATH = "/home/ubuntu/server/crypto_monitor"

def p(s):
    try: print(s)
    except UnicodeEncodeError: print(s.encode("ascii","replace").decode("ascii"))

def run(client, cmd):
    p(f"[*] {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=120)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8","replace")
    err = stderr.read().decode("utf-8","replace")
    if out.strip(): p(out.strip())
    if code != 0 and err.strip(): p(f"[-] {err.strip()}")
    return code, out

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)
scp = SCPClient(client.get_transport())
p("[+] 已连接")

dist_dir = os.path.join(BASE, "frontend", "dist")
zip_path = os.path.join(BASE, "frontend_dist.zip")
if os.path.exists(zip_path): os.remove(zip_path)
n = 0
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(dist_dir):
        for f in files:
            fp = os.path.join(root, f)
            zf.write(fp, os.path.relpath(fp, dist_dir))
            n += 1
p(f"[+] 打包 {n} 个文件")

scp.put(zip_path, "/tmp/frontend_dist.zip")
run(client, f"cd {PROJECT_PATH}/frontend && rm -rf assets && rm -f index.html && "
            "python3 -c \"import zipfile; zipfile.ZipFile('/tmp/frontend_dist.zip').extractall('.')\" && "
            "sudo chown -R ubuntu:ubuntu . && ls -la")
p("[+] 前端部署完成")
scp.close(); client.close()
os.remove(zip_path)
