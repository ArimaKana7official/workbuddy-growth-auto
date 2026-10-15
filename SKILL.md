---
title: "WorkBuddy 成长计划全自动助手"
summary: "每日签到 + 自动清成长计划任务（含小程序链与 PC 限定任务）+ 猫猫旅行积分 + 核验到账"
read_when:
  - 用户要求自动完成 WorkBuddy 成长计划 / 签到 / 积分任务
  - 定时任务需要清成长计划任务
  - 排查成长任务"做了但没点亮"的问题
---

# WorkBuddy 成长计划全自动助手

一套经过实测的完整方案：社区脚本做每日批量任务，UI 自动化兜底"PC 限定"任务，
定时任务每天凌晨自动跑并输出核验报告。2026-10 实测从 14/18 清到全清 + 等级 17→18。

## 快速开始：对 WorkBuddy 说的一段话

新用户把下面这段话**整段复制**发给自己的 WorkBuddy 即可，它会自动完成安装、
配置、试跑和定时任务创建（第 8 步的定时任务创建需要用户在客户端里确认）：

```text
帮我部署 WorkBuddy 成长计划全自动助手，严格按以下步骤执行：

1. 安装本技能：克隆 https://github.com/ArimaKana7official/workbuddy-growth-auto
   到 ~/.workbuddy/skills/workbuddy-growth-auto，然后阅读其中的 SKILL.md 作为本任务的执行手册。
2. 安装依赖技能：搜索并安装 totorosir-workbuddy-score（积分助手技能）。
3. 克隆社区脚本到工作区：git clone --depth 1 https://github.com/mryuanxiaojun/WorkBuddy-Daily.git
4. 对克隆下来的 workbuddy_daily.py 做安全审查（按 SKILL.md「安全与风险」一节）：
   确认外联域名仅腾讯系（tencent.com/qq.com/myqcloud.com）、无 exec/eval/subprocess
   动态执行、无可疑文件写操作。审查不通过就停下来向我报告，不要继续。
5. 按 SKILL.md「必打补丁」一节给脚本打 3 个补丁（禁真实桌面模式开关、
   /v2/report 裸数组、accept 锁定三态），打完做语法检查。
6. 用技能包 scripts/gen_tokens.py 从我本机登录态静默生成令牌库
   （token 绝不能显示在对话或日志里），然后只读试跑 --query 验证连通。
7. 手动完整试跑一次（WB_DAILY_NO_REAL_DESKTOP=1，--gap 2.0），给我看报告。
8. 试跑成功后，创建每天凌晨 1:00 的定时任务：提示词使用 SKILL.md 的
   「定时任务提示词模板」整段内容，并结合「PC 限定任务流程」一节。
   创建前把任务计划展示给我确认。
注意：全程不要把 wb_refresh_tokens.json 的内容输出到对话或写入任何会外传的地方。
```

## 方案组成（三层）

| 层 | 工具 | 覆盖 |
|---|---|---|
| 1. 主流程 | 社区脚本 [WorkBuddy-Daily](https://github.com/mryuanxiaojun/WorkBuddy-Daily)（已打补丁） | Token 续期、签到、云端/事件类任务、小程序 Sequential_Tasks 链、领奖、真实余额查询 |
| 2. 辅助 | totorosir-workbuddy-score 技能（buddy_station.py） | 幂等签到、猫猫旅行先领后派、活动口径积分 |
| 3. 兜底 | scripts/ui_helper.py（本技能） | 「PC 限定」等必须真实客户端动作的任务 |

## 前置条件

- Windows + 已登录的 WorkBuddy 桌面客户端（登录态在本机）
- Python 3.11+，`pip install requests pillow pywin32`（ui_helper 需要 pywin32）
- 已安装技能：`totorosir-workbuddy-score`（提供登录态解密与 buddy_station.py）

## 一次性配置（5 步）

```bash
# 1. 克隆社区脚本
git clone --depth 1 https://github.com/mryuanxiaojun/WorkBuddy-Daily.git

# 2. 安全审查（必做！见下"安全与风险"）：检查外联域名/动态执行/文件写操作
grep -n "https\?://" WorkBuddy-Daily/workbuddy_daily.py | grep -v "tencent.com\|qq.com\|myqcloud.com"
grep -n "exec(\|eval(\|subprocess\|os.system\|__import__\|pickle" WorkBuddy-Daily/workbuddy_daily.py

# 3. 打补丁（见下一节，3 个必打）

# 4. 从本机登录态静默生成令牌库（token 不落对话日志）
python scripts/gen_tokens.py <WorkBuddy-Daily目录>

# 5. 只读试跑，验证凭据与接口连通
WB_DAILY_NO_REAL_DESKTOP=1 python WorkBuddy-Daily/workbuddy_daily.py --query
```

## 必打补丁（原版脚本的 3 个坑，已实测）

1. **禁止真实桌面模式**（否则脚本会 taskkill WorkBuddy.exe，把宿主自动化会话一起杀掉）：
   在 `t_desktop_tasks` 开头加环境变量开关：
   ```python
   if os.environ.get("WB_DAILY_NO_REAL_DESKTOP"):
       is_win = False  # 强制走指纹上报降级
   ```
   运行时永远带 `WB_DAILY_NO_REAL_DESKTOP=1`。

2. **`/v2/report` 只接受裸事件数组**：web 事件（`report_web_event`）和 mini 事件
   （`_mini_report`）的 body 必须是 `[ev]`，不能是 `{"common":{...},"events":[...]}`
   信封——信封会被 400 "eventCode is empty" 或 200 但静默丢弃。
   同时补齐 web 指纹：头 `x-client-platform: web` + `X-User-Id` +
   `Referer=页面URL本身` + 完整 Chrome UA，事件内带 `enterpriseId: ""`。

3. **accept 三态识别**：`_mp_accept` 改为返回 `(status, message)`，
   识别服务端 `"task locked until YYYY-MM-DD"`（活动分日解锁，属正常待解锁，
   不是失败，别重试），任务链遍历 `Sequential_Tasks_1..7` 全部环。

## 定时任务提示词模板（可直接粘贴到 automation）

> 核心原则：一个自动化承载全流程；提示词必须自包含（脚本绝对路径、环境变量、
> 判断标准都写进去，因为定时执行时看不到本对话）。

```
1. 主流程：WB_DAILY_NO_REAL_DESKTOP=1 python <WorkBuddy-Daily>/workbuddy_daily.py --gap 2.0
   （托管 Python 绝对路径）。记录输出报告。
2. PC 限定任务（task_desc 含「在 PC 客户端内」）：接口上报无法点亮（服务端校验
   真实客户端遥测），走 UI 自动化（见 SKILL「PC 限定任务流程」）；屏幕锁定则跳过并注明。
3. 旅行：报告显示「已到达（待领取）」时运行
   buddy_station.py checkin --travel-auto --json --no-toast --no-push 先领后派；
   能量不足 10 无法重派则记录，次日自动补。
4. 核验：签到状态、各任务 completed/claimed、成长等级、真实余额（主套餐+加量包）
   与活动口径 total_credits 前后变化。
5. 报告区分未完成原因：锁定中 / 需真实客户端 / 能量不足。
```

## PC 限定任务流程（如「体验灵感功能」）

服务端校验真实客户端遥测（qimei36/真实会话），**伪造事件上报永远不计数**（实测：
换 web/桌面指纹、真实 device-id、提取 asar 全部 109 个事件码按真实载荷上报，全部无效）。
必须真实客户端动作，且**埋点关联有约 5-10 分钟延迟**：

1. **锁屏检测**：PIL ImageGrab 截图判断桌面是否可见，锁屏则放弃（输入注入在
   锁定桌面上无效），报告注明请用户白天补做。
2. **激活窗口**：`scripts/ui_helper.py`（已处理 DPI）。WorkBuddy 主窗口特征：
   title 为 "WorkBuddy"/"腾讯WorkBuddy" 且类名 `Chrome_WidgetWin*`，托盘最小化时
   hwnd rect 在 -16000，先 SW_RESTORE。可能有一个全屏黑色辅助窗口遮挡，需最小化。
3. **点击路径**：侧边栏「更多」→ 弹出菜单「灵感」→ 灵感页点第一个模板卡片进
   详情 → 右下角「做同款」→ 新任务页已预填模板 prompt → 点输入框聚焦后按 Enter 发送。
4. **领奖**：等 5-10 分钟轮询 `_mp_prog(s, code)` 到 `completed` 后 `_mp_claim`。
   坐标必须从当次全屏截图重新定位，**不可硬编码**（窗口位置/DPI 都会变）。

### 关键坑（踩过的）

- **DPI 虚拟化**：Python 进程非 DPI 感知时 `GetWindowRect` 返回虚拟坐标
  （物理=虚拟×缩放倍数），而 `SetCursorPos` 用物理坐标——两者错位点击全落空。
  务必 `ctypes.windll.user32.SetProcessDPIAware()`。
- **PrintWindow 的坑**：它按虚拟尺寸渲染，布局比例和实际不一致，坐标定位
  只信全屏截图（ImageGrab）。
- 发送模板任务优先用「聚焦输入框 + Enter」，比精确点击发送按钮稳。

## 排障速查

| 症状 | 原因与处理 |
|---|---|
| 上报 400 "eventCode is empty" | body 用了信封格式 → 改裸数组 `[ev]` |
| 上报 200 但进度不动 | 缺 `X-User-Id` 头或事件缺 `userId`（服务端 200 但静默丢弃）；或该任务是 PC 限定（走 UI 自动化） |
| accept 返回 error | 看 results[].message：`task locked until X` = 分日解锁，到日自动可做。锁定信息**只在 accept 响应里**，任务详情接口查不到 |
| 「使用 GLM5.2 模型」类小程序任务 | mp 口径：`X-Client-Platform: miniprogram` 头查询/报名，chat_request_send 事件带 `requestModelId: "glm-5.2"`，裸数组上报 |
| 猫猫旅行到达但没领 | 主流程只展示不领取，需 buddy_station `--travel-auto`；重派需能量 ≥10 |
| 活动积分 vs App 显示对不上 | 两个口径：`checkin-activity-status` 的 total_credits 是活动签到累计；App「我的」是真实余额（含用量扣减小数），以脚本输出的「积分」行为准 |

## 安全与风险（使用前必读）

- WorkBuddy-Daily 是非官方逆向接口脚本：腾讯改接口即失效（脚本带未适配任务
  检测，失效时输出 ⚠️）；存在理论上的账号风控风险。
- 令牌库 `wb_refresh_tokens.json` 含 refreshToken（90 天自动续期、自轮换），
  **绝不外传、不提交到 git、不写进对话/报告**；极端情况下可能需要客户端重新登录。
- 克隆任何第三方脚本后先做安全审查（外联域名、动态执行、文件写操作）再用。

## 本技能脚本

- `scripts/gen_tokens.py` — 从本机加密登录态生成令牌库（不回显 token）
- `scripts/list_growth.py` — 列出全部成长任务状态/进度/深链
- `scripts/ui_helper.py` — 客户端 UI 自动化辅助（DPI 感知：找窗口/激活/截图/点击/滚动）
