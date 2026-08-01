# -*- coding: utf-8 -*-
"""验证矩阵 API 返回数据是否与设计场景一致（独立辅助脚本）。"""
import re
import sys

import requests

BASE = "http://localhost:4000"
s = requests.Session()

# 1) GET /login 拿 nonce
r = s.get(BASE + "/login", timeout=15)
m = re.search(r'name="nonce"[^>]*value="([^"]+)"', r.text)
if not m:
    # 兼容 value 在前
    m = re.search(r'value="([^"]+)"[^>]*name="nonce"', r.text)
nonce = m.group(1) if m else None
print("nonce obtained:", bool(nonce))

# 2) POST /login
r = s.post(
    BASE + "/login",
    data={"name": "root", "password": "root", "nonce": nonce},
    timeout=15,
    allow_redirects=False,
)
print("login status:", r.status_code, "->", r.headers.get("Location"))

# 3) GET 矩阵 API
r = s.get(BASE + "/api/v1/statistics/progression/matrix", timeout=15)
print("matrix api status:", r.status_code)
data = r.json()["data"]

chal_id_to_name = {c["id"]: c["name"] for c in data["challenges"]}
# 列顺序按 displayChallenges 的 position 排序
chals_sorted = sorted(
    data["challenges"],
    key=lambda c: (
        c["position"] == 0,
        c["position"],
        c["value"],
        c["category"],
        c["id"],
    ),
)
col_names = [c["name"] for c in chals_sorted]
col_ids = [c["id"] for c in chals_sorted]
print("\n队伍数:", len(data["scoreboard"]), " 题目数:", len(data["challenges"]),
      " 组别数:", len(data["brackets"]))
print("组别:", [b["name"] for b in data["brackets"]])

print("\n=== 矩阵（按名次）===")
header = f"{'名次':<4}{'队伍':<12}{'得分':<6}" + "".join(f"{n:<10}" for n in col_names)
print(header)
print("-" * len(header))
for u in data["scoreboard"]:
    cells = []
    for cid in col_ids:
        if cid in u["solves"]:
            cells.append("✓解(绿)")
        elif cid in u["attempts"]:
            cells.append("试(黄)")
        elif cid in u["opens"]:
            cells.append("开(青)")
        else:
            cells.append("-(灰)")
    print(f"{u['place']:<4}{u['name']:<12}{u['score']:<6}" + "".join(f"{c:<10}" for c in cells))

print("\n=== 校验 ===")
expected = {
    "Gamma战队": (1, 1000, {"签到题", "栈溢出", "流量分析"}),
    "Alpha战队": (2, 600, {"签到题", "SQL注入", "RSA破解"}),
    "Beta战队": (3, 300, {"签到题", "SQL注入"}),
    "Omega战队": (4, 200, {"签到题", "隐写术"}),
    "Delta战队": (5, 100, {"签到题"}),
}
ok = True
for u in data["scoreboard"]:
    exp_place, exp_score, exp_solves = expected[u["name"]]
    got_solves = {chal_id_to_name[cid] for cid in u["solves"]}
    place_ok = u["place"] == exp_place
    score_ok = u["score"] == exp_score
    solves_ok = got_solves == exp_solves
    status = "OK" if (place_ok and score_ok and solves_ok) else "MISMATCH"
    if status == "MISMATCH":
        ok = False
    print(f"  {u['name']}: 名次={u['place']}(期{exp_place}) 得分={u['score']}(期{exp_score}) "
          f"解题={sorted(got_solves)} 期望={sorted(exp_solves)} -> {status}")

print("\n所有队伍数据关联校验:", "通过 ✓" if ok else "失败 ✗")
