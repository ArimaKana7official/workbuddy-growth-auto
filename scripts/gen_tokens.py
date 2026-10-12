# -*- coding: utf-8 -*-
"""从本机加密登录态生成 WorkBuddy-Daily 的 wb_refresh_tokens.json（不回显 token）。

用法：python gen_tokens.py [WorkBuddy-Daily目录]
- 默认自动探测当前目录及 ../WorkBuddy-Daily
- 依赖 totorosir-workbuddy-score 技能的解密能力（~/.workbuddy/skills/）
"""
import base64
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 定位 buddy_station（totorosir-workbuddy-score 技能）
CANDIDATES = [
    os.path.expanduser("~/.workbuddy/skills/totorosir-workbuddy-score/scripts"),
    os.path.expanduser("~/workbuddy/skills/totorosir-workbuddy-score/scripts"),
]
bs_dir = next((p for p in CANDIDATES if os.path.exists(
    os.path.join(p, "buddy_station.py"))), None)
if not bs_dir:
    print("未找到 totorosir-workbuddy-score 技能，请先安装："
          "~/.workbuddy/skills/totorosir-workbuddy-score/scripts/buddy_station.py")
    sys.exit(1)
sys.path.insert(0, bs_dir)
import buddy_station as bs  # noqa: E402

# 定位 WorkBuddy-Daily 输出目录
if len(sys.argv) > 1:
    daily_dir = sys.argv[1]
else:
    daily_dir = os.path.join(os.getcwd(), "WorkBuddy-Daily")
    if not os.path.isdir(daily_dir):
        daily_dir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "WorkBuddy-Daily")
if not os.path.isdir(daily_dir):
    print("未找到 WorkBuddy-Daily 目录，请先克隆："
          "git clone --depth 1 https://github.com/mryuanxiaojun/WorkBuddy-Daily.git")
    sys.exit(1)

path = bs.find_login_state()
if not path:
    print("未找到登录态，请先登录 WorkBuddy 客户端")
    sys.exit(1)
with open(path, "r", encoding="utf-8") as h:
    auth = json.load(h).get("auth", {})

at = bs.decrypt_access_token_field(auth["accessToken"])
rt = bs.decrypt_access_token_field(auth["refreshToken"]) if auth.get("refreshToken") else ""

# 从 AT payload 取手机号作为账号键
p = at.split(".")[1]
p += "=" * (4 - len(p) % 4)
user = json.loads(base64.urlsafe_b64decode(p)).get("preferred_username", "acct-1")

store_path = os.path.join(daily_dir, "wb_refresh_tokens.json")
store = {user: {"refresh_token": rt, "access_token": at}}
json.dump(store, open(store_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if os.name != "nt":
    os.chmod(store_path, 0o600)
print("OK: 已写入 %s，账号 %s（RT %s）" % (store_path, user, "已提取" if rt else "缺失"))
