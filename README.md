# nas-smb-cli

[English](README_EN.md) | 简体中文

NAS SMB 文件管理 CLI，基于 [smbprotocol](https://github.com/jborean93/smbprotocol) 实现，面向终端用户与 AI agent。无需挂载网络盘，直接在命令行浏览、传输和管理 NAS 共享中的文件。

## 特性

- **11 个子命令**：`ls` / `tree` / `stat` / `download` / `upload` / `mkdir` / `delete` / `move` / `read` / `find` / `df`
- **纯命令行、无交互**：所有参数一次给全，输出为纯文本，适合脚本与 AI agent 调用
- **报错清晰**：连接配置缺失时启动即提示缺哪个环境变量、如何设置；删除目录必须显式加 `--recursive`，防误删
- **零硬编码**：连接配置全部来自环境变量，代码与 README 中不包含任何真实凭据

## 环境要求

- Python 3.10+
- 依赖 [smbprotocol](https://pypi.org/project/smbprotocol/)（安装时自动带上）

## 安装

PyPI 发布 Coming soon，当前从源码安装：

```bash
git clone https://github.com/OstrichHermit/nas-smb-cli.git
cd nas-smb-cli
pip install .
```

安装后命令行会多一个 `nas` 命令。

## 配置

通过 4 个环境变量提供 NAS 连接信息，缺一不可：

| 环境变量 | 含义 | 示例（占位值） |
|----------|------|----------------|
| `NAS_HOST` | NAS 地址（IP 或主机名） | `192.168.1.100` |
| `NAS_USER` | SMB 用户名 | `user` |
| `NAS_PASSWORD` | SMB 密码 | `pass` |
| `NAS_SHARE` | 共享名 | `share` |

Windows 持久化设置（对新开的进程生效）：

```powershell
setx NAS_HOST "192.168.1.100"
setx NAS_USER "user"
setx NAS_PASSWORD "pass"
setx NAS_SHARE "share"
```

Linux / macOS：

```bash
export NAS_HOST="192.168.1.100"
export NAS_USER="user"
export NAS_PASSWORD="pass"
export NAS_SHARE="share"
```

配置缺失时运行任何子命令都会立即报错退出（exit 1），并列出缺少的变量名：

```text
error: 缺少 NAS 连接配置环境变量: NAS_HOST, NAS_SHARE
需要设置以下 4 个环境变量: NAS_HOST NAS_USER NAS_PASSWORD NAS_SHARE
示例: setx NAS_HOST "192.168.1.100"; ...
```

## 命令总览

| 命令 | 参数 | 说明 |
|------|------|------|
| `nas ls` | `[path]` | 列目录内容，目录在前、按名排序；缺省列共享根目录 |
| `nas tree` | `[path]` `--depth N` | 目录树，默认深度 3 |
| `nas stat` | `<path>` | 文件/目录信息：类型、大小、创建/修改/访问时间 |
| `nas download` | `<remote> <local>` | 下载文件；`local` 为目录时自动沿用远端文件名 |
| `nas upload` | `<local> <remote>` | 上传文件 |
| `nas mkdir` | `<path>` | 创建目录（含父目录） |
| `nas delete` | `<path>` `--recursive` | 删除文件；目录必须加 `--recursive`（别名 `--rmrf`） |
| `nas move` | `<src> <dst>` | 重命名/移动 |
| `nas read` | `<path>` `--bytes N` | 读取文本文件（UTF-8）；`--bytes N` 只读前 N 字节 |
| `nas find` | `[path]` `--name <pattern>` | 递归按名查找，fnmatch 通配符（如 `*.jpg`），大小写不敏感 |
| `nas df` | — | NAS 总容量/已用/可用 |

用法示例：

```bash
nas ls                                # 列共享根目录
nas ls Downloads                      # 列子目录
nas tree Backup --depth 2             # 目录树
nas stat Downloads/example.bin        # 文件/目录信息
nas download nas_path local_path      # 下载
nas upload local_path nas_path        # 上传
nas mkdir path/to/dir                 # 创建目录（含父目录）
nas delete path --recursive           # 删除目录树
nas move old new                      # 重命名/移动
nas read doc.txt --bytes 4096         # 读文本文件
nas find . --name "*.jpg"             # 按名查找
nas df                                # 容量
```

## 安全提示

- 建议为 CLI 使用**只读账号或最小权限账号**，避免误操作影响重要数据
- 不要把真实凭据写进代码、脚本或提交到版本库；一律走环境变量
- `delete` 对目录要求显式 `--recursive`，但请依然谨慎使用

## License

[MIT](LICENSE)
