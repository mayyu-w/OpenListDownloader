# OpenListDownloader

![Release](https://img.shields.io/badge/release-v1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10+-yellow)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

OpenList 文件下载器是一个基于 PyQt6 的桌面客户端，用于从 [OpenList](https://oplist.org/)（AList fork）网盘浏览和批量下载文件，通过 aria2 实现高速下载。

## 功能特性

- **服务器连接** — 支持 OpenList / AList v3 API，登录后自动管理 Token，过期自动重新登录
- **文件扫描** — 递归扫描远程目录，支持按文件后缀过滤（如 `.mp4,.mkv`），后台线程运行不阻塞界面
- **aria2 集成** — 一键启动/关闭 aria2，通过 JSON-RPC 管理下载任务，支持批量添加
- **配置持久化** — 自动保存服务器地址、扫描路径、aria2 配置，支持一键加载
- **日志归档** — 按天归档日志，自动清理 90 天以上的旧日志

## 截图

![Screenshot](assets/icon.png)

## 快速开始

### 环境要求

- Python 3.10+
- Windows 10/11
- [aria2](https://github.com/aria2/aria2)（可选，用于下载）

### 安装

```bash
git clone https://github.com/mayyu0203/OpenListDownloader.git
cd OpenListDownloader
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

### 使用步骤

1. 在「服务器连接」区域输入 OpenList 地址、用户名、密码，点击「连接」
2. 在「文件扫描」区域输入远程路径和文件后缀，点击「扫描文件」
3. 在「aria2 配置」区域设置 aria2 路径和下载目录，点击「启动 aria2」
4. 在文件列表中勾选需要下载的文件，点击「开始下载」

## 项目结构

```
OpenListDownloader/
├── main.py                  # 应用入口
├── config.py                # 全局常量
├── requirements.txt         # 依赖
├── assets/                  # 图标资源
├── core/
│   ├── api_client.py        # OpenList API 客户端
│   ├── token_manager.py     # Token 生命周期管理
│   ├── file_scanner.py      # 递归文件扫描器
│   └── aria2_rpc.py         # aria2 JSON-RPC 封装
├── gui/
│   ├── main_window.py       # 主窗口
│   ├── login_widget.py      # 服务器连接面板
│   ├── file_list_widget.py  # 文件列表面板
│   ├── aria2_widget.py      # aria2 配置面板
│   └── styles.py            # QSS 样式表
└── utils/
    ├── config_manager.py    # 配置持久化
    ├── format.py            # 格式化工具
    └── logger.py            # 日志管理
```

## 技术栈

- **GUI**: PyQt6
- **HTTP**: requests
- **下载引擎**: aria2 (JSON-RPC)
- **API**: OpenList / AList v3 REST API

## License

本项目基于 [MIT License](LICENSE) 开源。
