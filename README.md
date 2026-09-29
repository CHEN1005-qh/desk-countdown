# Desk Countdown

一个常驻桌面的「日期倒计时 + 番茄钟」二合一工具，安静置顶、到点响铃。

> 目标平台：Windows 10 / 11（64 位）  
> 技术栈：Python 3.10+ / PyQt6

---

## 功能

### 事件倒计时
- 管理多个目标日期（考试、节日、纪念日）
- 按剩余时间自动排序，已到期事件置后高亮
- 8 种颜色标签，秒级实时刷新
- 新建 / 编辑 / 删除（到期事件免确认）

### 时长计时
- 自定义倒计时：快捷按钮（5 / 10 / 15 / 25 / 30 / 45 / 60 分钟）
- ±1 / ±5 分钟微调
- 大数字显示 + 水平进度条

### 番茄钟
- 专注 / 短休息 / 长休息自动循环
- 环形进度条 + 番茄进度点
- 今日番茄数与累计统计
- 支持跳过、重置

### 铃声与提醒
- 3 种内置铃声（清脆短促 / 轻柔长音 / 复古电子）
- 音量调节、试听
- 可导入本地 MP3 / WAV
- 计时归零弹层提醒 + 任务栏闪烁

### 窗口与系统
- 始终置顶（图钉开关）
- 深色 / 浅色双主题一键切换
- 三档自适应布局（320px ~ 全屏）
- 透明度调节 + 鼠标悬停增强
- 系统托盘（最小化、暂停/继续、退出）
- 窗口位置与大小记忆
- 可选开机自启

---

## 安装与运行

### 方法一：直接运行源码

```bash
# 克隆仓库
git clone https://github.com/<your-username>/desk-countdown.git
cd desk-countdown

# 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

### 方法二：使用打包好的 exe

下载 Release 中的 `countdown.exe`，双击即可运行，无需安装 Python。

> 首次运行会在 exe 同目录创建 `data/` 文件夹存储事件、设置和统计数据（便携语义）。

---

## 打包

```bash
pyinstaller --onefile --windowed --name countdown --add-data "resources;resources" main.py
```

打包结果位于 `dist/countdown.exe`。

---

## 项目结构

```
desk-countdown/
├── main.py                  # 入口
├── requirements.txt         # 依赖
├── core/                    # 核心逻辑
│   ├── events.py            # 事件仓库
│   ├── settings.py          # 设置管理
│   ├── stats.py             # 专注统计
│   ├── timer_engine.py      # 倒计时引擎
│   ├── pomodoro.py          # 番茄钟状态机
│   ├── ringtone.py          # 铃声管理
│   └── paths.py             # 路径管理
├── ui/                      # 界面
│   ├── main_window.py       # 主窗口
│   ├── event_page.py        # 事件列表页
│   ├── event_dialog.py      # 新建/编辑对话框
│   ├── timer_page.py        # 计时页
│   ├── settings_dialog.py   # 设置对话框
│   ├── reminder_popup.py    # 提醒弹层
│   └── theme.py             # 主题管理
├── resources/               # 内置资源
│   └── ringtones/           # 3 个默认铃声
├── tests/                   # 单元测试
├── tools/                   # 工具脚本
└── data/                    # 运行时生成（被 .gitignore 忽略）
```

---

## 测试

```bash
pytest tests/ -v
```

覆盖事件、设置、计时引擎、番茄钟、统计五个模块。

---

## 许可证

MIT License
