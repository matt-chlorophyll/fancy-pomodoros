# Fancy Pomodoro CLI — 设计文档

- 日期：2026-05-22
- 状态：已确认，待写实现计划

## 1. 概述与目标

一个有设计感的命令行番茄钟，名为 `pomo`。两个核心目标：

1. **辅助专注**：每次做正事至少坚持一个 25 分钟，且允许超过。
2. **记录时间花费**：自动记录每个 session 的任务、分类与耗时，之后可复盘"每天在哪些事上花了多少时间"。

在满足需求的基础上，界面追求"极简优雅 + 一点互动感"，让用户用得开心。

## 2. 非目标（明确不做）

- 经典番茄循环（强制 5 分钟休息、4 个后长休息）。
- streak、热力图、周对比等趋势分析（本次只做 `report`，趋势留待以后）。
- 系统级通知（只用终端响铃）。
- 跨平台键盘支持（本期仅 Windows，但代码留好接口）。
- 编辑/删除历史 session、数据同步。

## 3. 技术栈

- Python 3.11+
- `rich` —— 界面渲染（`Live` 原地刷新）
- `typer` —— 命令解析与 `--help`
- 键盘输入用标准库 `msvcrt`（Windows 非阻塞轮询）

架构选择：用 **Rich + `Live`** 而非 Textual 全 TUI 应用——更轻、启动快，`pomo` 像一条正常 CLI 命令，跑完即回到 shell。

## 4. CLI 命令

| 命令 | 作用 |
|------|------|
| `pomo` / `pomo start` | 开一次专注 session |
| `pomo start --minutes 50` | 自定义本次目标时长（默认 25） |
| `pomo report` | 今日复盘报表 |
| `pomo report --week` | 本周（周一至周日）报表 |
| `pomo report --date 2026-05-20` | 指定某日报表 |

`pomo` 不带子命令时等同 `pomo start`。

## 5. Session 生命周期

```
pomo
  → 选分类       数字快速选已有分类，或输入新分类
  → 输入任务名    自由文本，提示该分类下最近用过的任务
  → 准备 3·2·1   约 3.5 秒的小仪式
  → 倒计时 25:00 极简画面：分类·任务 / 大号时间 / 进度条 / 一句鼓励
  → 归零         终端响一声 + 配色由冷转暖，无缝转「加时 +mm:ss」正计时
  → 用户按 s     弹出结束卡片：本次时长 / 今日累计 / 分类分布
```

### 进行中的按键（屏幕底部暗色小字提示）

- `空格` —— 暂停 / 继续
- `s` 或 `回车` —— 完成并记录
- `Esc` —— 放弃本次（不记录，二次确认）

### 规则

- 25 分钟是目标不是硬锁：不到 25 分钟也可按 `s` 停止并记录实际时长。
- `Ctrl-C` 视作"完成并记录"，不丢数据。
- 暂停期间不计入专注时长。

## 6. Session 状态机（`timer.py`）

`FocusTimer` 负责计时逻辑，不涉及渲染。

- `phase ∈ {FOCUS, OVERTIME}`，外加正交的 `is_paused` 布尔。
- 内部记录：起始单调时钟值、`target_seconds`、累计暂停秒数（及当前暂停起点）。
- `elapsed_focus = (now - start) - 累计暂停`。
- `phase = FOCUS if elapsed_focus < target_seconds else OVERTIME`。
- FOCUS 阶段提供 `remaining`；OVERTIME 阶段提供 `overtime`。
- 时钟通过构造参数注入（默认 `time.monotonic`），便于测试。
- 墙钟时间（`started_at` / `ended_at`）单独用 `datetime.now()` 记录。

## 7. 数据模型与存储

### Session 记录

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | str | 基于时间戳生成的唯一 id |
| `category` | str | 分类 |
| `task` | str | 任务名 |
| `started_at` | str | ISO8601 本地时间 |
| `ended_at` | str | ISO8601 本地时间 |
| `focus_seconds` | int | 实际专注秒数（不含暂停） |
| `target_seconds` | int | 本次目标时长（默认 1500） |
| `reached_overtime` | bool | 是否进入加时 |

### 存储

- 文件：`~/.fancy-pomodoro/sessions.json`，可用环境变量 `POMO_DATA_DIR` 覆盖目录。
- 格式：`{"version": 1, "sessions": [ ... ]}`，便于未来迁移。
- 写入用"临时文件 + 重命名"实现原子写，避免写坏。
- 分类列表从历史 `sessions` 自动汇总，不单独维护文件。

## 8. `pomo report` 报表

`stats.py` 提供纯聚合函数（可测）：按日期范围过滤、按分类汇总、按任务汇总、求总计与最长 session。`ui/report.py` 负责渲染，配色与专注界面一致。

示例输出：

```
  2026-05-22  今日复盘                    总计 3:47

  工作   ████████████████░░░░░░  2:30   ·  4 个 session
  学习   ███████░░░░░░░░░░░░░░░  1:05   ·  2 个
  副业   ██░░░░░░░░░░░░░░░░░░░░  0:12   ·  1 个

  最长一段   写设计文档 · 工作 · 52 分钟
```

无数据时显示友好的空状态提示。

## 9. 界面设计（极简优雅）

- 专注画面：分类·任务一行 → 大号时间居中（`1 8 : 4 2` 间隔字符 + 圆角面板）→ 进度条 → 一句轮换的鼓励语。
- 配色两套（`ui/theme.py`）：FOCUS 用冷色（柔和青/灰蓝），OVERTIME 转暖色（柔和琥珀）。
- 互动小细节：开始的 3·2·1 仪式、归零时响铃与配色切换、结束的总结卡片。
- 终端过窄时画面自适应收缩。

## 10. 代码结构

每个文件单一职责，纯逻辑与渲染分离。

```
fancy-pomodoros/
  pyproject.toml
  README.md
  pomo/
    __init__.py
    __main__.py     支持 python -m pomo
    cli.py          Typer 命令入口（start / report），驱动 tick 循环
    config.py       数据目录解析、默认时长、常量
    models.py       Session 数据类 + 序列化
    storage.py      sessions.json 的原子读写
    timer.py        FocusTimer 状态机（注入时钟，可测）
    keyboard.py     非阻塞按键读取（Windows msvcrt，留好跨平台接口）
    stats.py        聚合逻辑：按分类/任务/日期范围汇总
    ui/
      __init__.py
      theme.py      极简优雅配色（冷/暖两套）
      prompts.py    分类选择 + 任务输入 + 3·2·1 仪式
      countdown.py  专注/加时实时画面 + 结束卡片
      report.py     报表渲染
  tests/
    test_models.py
    test_storage.py
    test_timer.py
    test_stats.py
```

## 11. 错误处理与边界

- `sessions.json` 损坏或不存在 → 友好提示并以空数据起步；真正保存时把损坏文件备份为 `sessions.json.bak`，不静默覆盖。
- 终端过窄 → 画面自适应收缩。
- `Ctrl-C` 进行中 → 视作完成并保存。
- 放弃 session 走二次确认，避免误触丢进度。
- `pomo report` 指定日期无记录 → 空状态提示。

## 12. 测试策略

- `test_timer`：注入假时钟，验证 25 分钟处 FOCUS→OVERTIME 切换、暂停不计时、remaining/overtime 计算。
- `test_storage`：读写往返、损坏文件处理、原子写、文件缺失。
- `test_stats`：聚合正确性、日期过滤、周边界、最长 session。
- `test_models`：序列化往返。

## 13. 已定默认值

- 界面框架：Rich（非 Textual）。
- 数据位置：`~/.fancy-pomodoro/`（可被 `POMO_DATA_DIR` 覆盖）。
- 存储格式：带 `version` 的 JSON。
- 默认专注时长：25 分钟，`pomo start --minutes N` 可改。
