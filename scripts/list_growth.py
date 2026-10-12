# -*- coding: utf-8 -*-
"""列出全部成长计划任务：状态/进度/标题/跳转深链。

用法：python list_growth.py
依赖本机 WorkBuddy 客户端登录态（totorosir-workbuddy-score 技能解密）。
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CANDIDATES = [
    os.path.expanduser("~/.workbuddy/skills/totorosir-workbuddy-score/scripts"),
    os.path.expanduser("~/workbuddy/skills/totorosir-workbuddy-score/scripts"),
]
bs_dir = next((p for p in CANDIDATES if os.path.exists(
    os.path.join(p, "buddy_station.py"))), None)
if not bs_dir:
    print("未找到 totorosir-workbuddy-score 技能")
    sys.exit(1)
sys.path.insert(0, bs_dir)
import buddy_station as bs  # noqa: E402

token, domain, headers = bs._resolve_auth("auto")
if headers:
    bs._AUTH_HEADERS = headers
status, body = bs.api_call(domain, token, "/v2/activity/growth/tasks", method="GET")
for t in body["data"]["tasks"]:
    p = t.get("progress") or {}
    print("%-22s | %-14s | %s/%s | %s | %s" % (
        t["task_code"], t.get("accept_status"), p.get("current"), p.get("target"),
        t["title"], t.get("jump_url")))
