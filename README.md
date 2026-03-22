# openpilot-ui
<<<<<<< HEAD
openpilot的ui设计，独立与算法部分，
=======

从 [openpilot](https://github.com/commaai/openpilot) 项目中提取的独立 UI 应用，保留了完整的用户界面功能和代码结构。

<img width="2162" height="1119" alt="image" src="https://github.com/user-attachments/assets/59af8be3-4362-413e-ae93-d6150af43f22" />

<img width="2162" height="1119" alt="image" src="https://github.com/user-attachments/assets/6eabfcd0-6db1-46d2-acee-83f11a005e94" />

<img width="2162" height="1119" alt="image" src="https://github.com/user-attachments/assets/1ac00fa6-0fba-40db-8f04-e171281db333" />



## 特性

- **完整的 UI 功能**: 保留所有原版 UI 组件
  - 行驶中界面 (摄像头画面、路径渲染、HUD、警报)
  - 设置面板 (设备、网络、开关、软件、开发者)
  - 主页界面和侧边栏
  - 引导流程

- **模拟数据支持**: 可在没有真实车辆的情况下运行演示
  - 模拟车辆状态 (速度、转向)
  - 模拟模型输出 (路径、车道线、前车)
  - 模拟传感器数据

- **保持原有架构**:
  - cereal 消息系统
  - msgq 消息队列
  - raylib 渲染引擎

## 快速开始

### 1. 安装依赖

```bash
# 系统依赖 (Ubuntu/Debian)
sudo apt install capnproto libcapnp-dev

# Python 依赖
pip install -e .
```

### 2. 运行模拟模式

```bash
# 方式一：使用启动脚本
python -m openpilot.tools.sim.run_ui --mode demo # 放大模式# BIG=1 SCALE=1.5

# 方式二：分别启动
# 终端 1: 启动模拟数据
python -m openpilot.selfdrive.mock.data_simulator

# 终端 2: 启动 UI
python -m openpilot.selfdrive.ui.ui
```

### 3. 运行选项

```bash
# 使用真实摄像头
python -m openpilot.tools.sim.run_ui --mode camera --device 0

# 指定显示尺寸
python -m openpilot.tools.sim.run_ui --width 1920 --height 1080

# 全屏模式
python -m openpilot.tools.sim.run_ui --fullscreen
```

## 项目结构

```
openpilot-ui/
├── cereal/              # 消息定义和 messaging 系统
├── msgq/                # 消息队列和 VisionIpc
├── common/              # 通用工具和变换函数
├── system/ui/           # UI 核心库
│   ├── lib/             # 应用框架、着色器、文本测量
│   └── widgets/         # 按钮、开关、键盘等组件
├── selfdrive/ui/        # 主 UI 应用
│   ├── layouts/         # 主布局、设置面板、侧边栏
│   ├── onroad/          # 行驶中界面组件
│   ├── widgets/         # UI 控件
│   └── assets/          # 字体、图标、图片
├── selfdrive/mock/      # 模拟数据提供者
└── tools/sim/           # 启动脚本
```

## 模拟数据

模拟数据模块 (`selfdrive/mock/`) 提供以下发布者：

| 模块 | 发布的消息 | 说明 |
|------|-----------|------|
| `mock_card.py` | carState, controlsState | 车辆状态 |
| `mock_modeld.py` | modelV2, liveCalibration | 模型预测 |
| `mock_selfdrive.py` | selfdriveState, radarState | 驾驶状态 |
| `mock_sensord.py` | deviceState, pandaStates | 设备和传感器 |

## 界面操作

### 键盘快捷键

- `Space` - 切换启用/停用状态
- `E` - 切换实验模式
- `M` - 切换公制/英制单位
- `Esc` - 退出

### 触摸/鼠标操作

- 点击设置图标打开设置面板
- 点击侧边栏图标显示/隐藏状态信息
- 在设置面板中滑动切换选项

## 从原项目更新

```bash
# 复制最新的 UI 代码
cp -r ../openpilot/system/ui ./system/
cp -r ../openpilot/selfdrive/ui ./selfdrive/
cp -r ../openpilot/selfdrive/assets ./selfdrive/

# 更新消息定义
cp ../openpilot/cereal/log.capnp ./cereal/
cp -r ../openpilot/cereal/messaging ./cereal/
```

## 与原项目的关系

- **代码来源**: 直接从 commaai/openpilot 复制
- **更新方式**: 可以从原项目同步更新
- **独立性**: 不依赖完整 openpilot 运行环境
- **许可证**: 遵循 openpilot 的 MIT 许可证

## 架构说明

```
┌─────────────────────────────────────────────────────────────┐
│                     Mock Data Publishers                     │
│              (mock_card, mock_modeld, ...)                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              cereal / msgq / VisionIpc                       │
│                  (消息传递基础设施)                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     UI (Python/raylib)                       │
│   ui_state.py → layouts/ → settings/                        │
│               → onroad/                                     │
└─────────────────────────────────────────────────────────────┘
```

## 系统要求

- Python 3.12+
- OpenGL ES 3.0 或 OpenGL 3.3
- capnproto

## 故障排除

### 找不到模块

确保在项目根目录运行，或设置 PYTHONPATH：

```bash
export PYTHONPATH=/path/to/openpilot-ui:$PYTHONPATH
```

### 字体加载失败

确保字体文件存在：

```bash
ls selfdrive/assets/fonts/*.fnt
```

### 黑屏

检查是否启动了数据模拟器：

```bash
python -m openpilot.selfdrive.mock.data_simulator &
python -m openpilot.selfdrive.ui.ui
```

## 许可证

MIT License - 基于 [commaai/openpilot](https://github.com/commaai/openpilot)
>>>>>>> feat-3.22-new
