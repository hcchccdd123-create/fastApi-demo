# 🚀 FastAPI 项目运维手册（Linux）

## 📦 项目基本信息

* 项目路径：`/root/fastapi-demo`
* 服务名称：`fastapi-demo`
* 端口：`8000`
* 启动方式：`systemd + gunicorn`
* Python 环境：`.venv`

---

# 🧠 一、服务管理（最常用）

## ▶️ 启动服务

```bash
systemctl start fastapi-demo
```

---

## ⏹ 停止服务

```bash
systemctl stop fastapi-demo
```

---

## 🔄 重启服务（最常用）

```bash
systemctl restart fastapi-demo
```

👉 每次代码更新后必须执行

---

## 📊 查看服务状态

```bash
systemctl status fastapi-demo
```

看到：

```text
Active: active (running)
```

说明服务正常

---

# 📜 二、日志查看

## 🔴 实时日志（最重要）

```bash
journalctl -u fastapi-demo -f
```

👉 类似“实时控制台输出”

---

## 📄 查看最近日志

```bash
journalctl -u fastapi-demo -n 50
```

---

## ⏱ 按时间查看

```bash
journalctl -u fastapi-demo --since "10 minutes ago"
```

---

# 🌐 三、接口访问

## Swagger 文档

```text
http://服务器IP:8000/docs
```

---

## 健康检查

```bash
curl http://127.0.0.1:8000/
```

---

# 🔧 四、端口与进程检查

## 查看端口监听

```bash
ss -lntp | grep 8000
```

---

## 查看进程

```bash
ps -ef | grep gunicorn
```

---

# 📦 五、代码更新（发版流程）

## 1️⃣ 本地修改代码

例如：

```text
app/api/auth.py
```

---

## 2️⃣ 上传到服务器

路径：

```text
/root/fastapi-demo/app/api/
```

---

## 3️⃣ 重启服务

```bash
systemctl restart fastapi-demo
```

---

## 4️⃣ 验证是否生效

```bash
systemctl status fastapi-demo
```

或访问：

```text
http://服务器IP:8000/docs
```

---

# 🧪 六、Redis 测试

```bash
redis-cli ping
```

返回：

```text
PONG
```

---

# ⚠️ 七、常见问题

## ❌ 服务启动失败

查看日志：

```bash
journalctl -u fastapi-demo -f
```

---

## ❌ 修改代码不生效

👉 忘记重启服务

```bash
systemctl restart fastapi-demo
```

---

## ❌ 端口无法访问

检查：

* 云安全组是否放行 8000
* 服务是否监听成功

---

## ❌ Redis 不生效

检查：

```bash
systemctl status redis
```

---

# 🧹 八、虚拟环境（仅首次部署）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

# 📁 九、项目结构（服务器）

```text
/root/fastapi-demo
├── app/
├── .venv/
├── app.db
├── requirements.txt
└── .env
```

---

# 🎯 十、重要说明

* 不要上传 `.venv`（服务器单独创建）
* 每次修改代码必须重启服务
* 日志统一通过 `journalctl` 查看
* Redis 控制 token 失效

---

# 🚀 后续可扩展

* Nginx 反向代理（80端口）
* HTTPS（域名 + SSL）
* Docker 部署
* CI/CD 自动发版
* 日志文件化

---
