# Fancy Pomodoro

一个极简优雅的命令行番茄钟，辅助专注并自动记录时间花费。

## 安装

需要 Python 3.11+。

    python -m venv .venv
    .venv/Scripts/python -m pip install -e .

安装后 `pomo` 命令位于 `.venv/Scripts/`。把该目录加入 PATH，或用
`pipx install .` 全局安装，即可在任意目录直接敲 `pomo`。

## 使用

    pomo                     # 开一次 25 分钟专注 session
    pomo start --minutes 50  # 自定义本次目标时长
    pomo report              # 今日复盘
    pomo report --week       # 本周复盘
    pomo report --date 2026-05-20

session 进行中：`空格` 暂停 / 继续，`s` 完成并记录，`Esc` 放弃本次。
25 分钟到点后会响一声并无缝转入加时正计时，做完按 `s` 收尾。

## 数据

每次 session 记录到 `~/.fancy-pomodoro/sessions.json`（人类可读的 JSON）。
可用环境变量 `POMO_DATA_DIR` 改变存储目录。

## 开发

    .venv/Scripts/python -m pip install -e ".[dev]"
    .venv/Scripts/python -m pytest

设计与实现文档见 `docs/superpowers/`。
