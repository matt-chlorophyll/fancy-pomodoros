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
    pomo start --minutes 50  # 自定义本次专注时长
    pomo rest                # 开一次 5 分钟休息 session
    pomo rest --minutes 10   # 自定义本次休息时长
    pomo superfocus          # 硬性专注：focus 不足 25 分钟会被丢弃
    pomo sf                  # 同上，简写
    pomo report              # 今日复盘
    pomo report --week       # 本周复盘
    pomo report --date 2026-05-20

session 进行中：`空格` 暂停 / 继续，`s` 完成并记录，`Esc` 放弃本次。
到点后会响一声并无缝转入加时正计时，做完按 `s` 收尾。

`superfocus`/`sf` 模式下，未到 25 分钟就按 `s` 会被直接丢弃、不记录——
用来逼自己把专注做满最小长度。

专注加时显示绿色（更长的专注是好事）；休息加时显示红色（该回来工作了）。
复盘里专注和休息分块展示，专注的累计时长不包含休息。

## 数据

每次 session 记录到 `~/.fancy-pomodoro/sessions.json`（人类可读的 JSON）。
可用环境变量 `POMO_DATA_DIR` 改变存储目录。

## 开发

    .venv/Scripts/python -m pip install -e ".[dev]"
    .venv/Scripts/python -m pytest

设计与实现文档见 `docs/superpowers/`。
