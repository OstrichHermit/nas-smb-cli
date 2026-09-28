#!/usr/bin/env python3
"""NAS SMB 文件管理 CLI（smbprotocol 实现）

用法示例：
  nas ls                                # 列共享根目录
  nas ls Downloads                      # 列子目录
  nas tree Backup --depth 2             # 目录树
  nas stat Downloads/example.bin        # 文件/目录信息
  nas download nas_path local_path      # 下载
  nas upload local_path nas_path        # 上传
  nas mkdir path/to/dir                 # 创建目录（含父目录）
  nas delete path --recursive           # 删除（--recursive 删目录树）
  nas move old new                      # 重命名/移动
  nas read doc.txt --bytes 4096         # 读文本文件
  nas find . --name "*.jpg"             # 按名查找（fnmatch）
  nas df                                # NAS 总容量/已用/可用

连接配置通过环境变量提供（缺一不可）：
  NAS_HOST       NAS 地址
  NAS_USER       用户名
  NAS_PASSWORD   密码
  NAS_SHARE      共享名
"""
import argparse
import fnmatch
import io
import logging
import os
import socket
import sys

import smbclient

SERVER = os.environ.get('NAS_HOST', '')
USER = os.environ.get('NAS_USER', '')
PWD = os.environ.get('NAS_PASSWORD', '')
SHARE = os.environ.get('NAS_SHARE', '')

socket.setdefaulttimeout(30)
logging.getLogger('smbprotocol').setLevel(logging.ERROR)


def ensure_config():
    required = {'NAS_HOST': SERVER, 'NAS_USER': USER, 'NAS_PASSWORD': PWD, 'NAS_SHARE': SHARE}
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f'error: 缺少 NAS 连接配置环境变量: {", ".join(missing)}', file=sys.stderr)
        print('需要设置以下 4 个环境变量: NAS_HOST NAS_USER NAS_PASSWORD NAS_SHARE', file=sys.stderr)
        print('示例: setx NAS_HOST "192.168.1.100"; setx NAS_USER "user"; setx NAS_PASSWORD "pass"; setx NAS_SHARE "share"', file=sys.stderr)
        sys.exit(1)


def unc(path=''):
    p = f'\\\\{SERVER}\\{SHARE}'
    if path:
        p += '\\' + path.strip('\\/')
    return p


def get_size(entry):
    try:
        return entry.stat().st_file_size
    except Exception:
        try:
            return entry.stat().st_size
        except Exception:
            return 0


def fmt_size(n):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1024 or unit == 'TB':
            return f'{n:.1f}{unit}' if unit != 'B' else f'{n}B'
        n /= 1024


def cmd_ls(args):
    p = unc(args.path)
    entries = sorted(smbclient.scandir(p), key=lambda e: (not e.is_dir(), e.name.lower()))
    for e in entries:
        if e.is_dir():
            print(f'  [DIR]  {e.name}')
        else:
            print(f'  {fmt_size(get_size(e)):>9}  {e.name}')


def cmd_tree(args):
    def walk(p, prefix, depth):
        if depth > args.depth:
            return
        entries = sorted(smbclient.scandir(p), key=lambda e: (not e.is_dir(), e.name.lower()))
        dirs = [e for e in entries if e.is_dir()]
        files = [e for e in entries if not e.is_dir()]
        for e in files:
            print(f'{prefix}  {fmt_size(get_size(e)):>9}  {e.name}')
        for e in dirs:
            print(f'{prefix}  [DIR]  {e.name}')
            walk(p + '\\' + e.name, prefix + '    ', depth + 1)

    root = unc(args.path)
    print(f'[DIR]  {args.path or SHARE}')
    walk(root, '    ', 1)


def cmd_stat(args):
    p = unc(args.path)
    st = smbclient.stat(p)
    isdir = smbclient.path.isdir(p)
    print(f'path:  {args.path}')
    print(f'type:  {"directory" if isdir else "file"}')
    if not isdir:
        print(f'size:  {fmt_size(st.st_size)} ({st.st_size} bytes)')
    import datetime
    for label, ts in (('created', st.st_ctime), ('modified', st.st_mtime), ('accessed', st.st_atime)):
        if ts:
            print(f'{label}: {datetime.datetime.fromtimestamp(ts):%Y-%m-%d %H:%M:%S}')


def cmd_df(args):
    r = smbclient.stat_volume(unc(''))
    total, free = r.total_size, r.actual_available_size
    used = total - free
    print(f'总容量:   {fmt_size(total)}')
    print(f'已用:     {fmt_size(used)} ({used / total * 100:.1f}%)')
    print(f'可用:     {fmt_size(free)}')


def cmd_download(args):
    src, dst = unc(args.remote), args.local
    if os.path.isdir(dst) or dst.endswith(('/', '\\')) or dst == '.':
        dst = os.path.join(dst, os.path.basename(args.remote))
    n = 0
    with smbclient.open_file(src, mode='rb') as f, open(dst, 'wb') as out:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            n += len(chunk)
    print(f'downloaded {fmt_size(n)} -> {dst}')


def cmd_upload(args):
    src, dst = args.local, unc(args.remote)
    n = 0
    with open(src, 'rb') as f, smbclient.open_file(dst, mode='wb') as out:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            n += len(chunk)
    print(f'uploaded {fmt_size(n)} -> {dst}')


def cmd_mkdir(args):
    smbclient.makedirs(unc(args.path))
    print(f'created {args.path}')


def rmtree(p):
    for e in smbclient.scandir(p):
        full = p + '\\' + e.name
        if e.is_dir():
            rmtree(full)
        else:
            smbclient.remove(full)
    smbclient.rmdir(p)


def cmd_delete(args):
    p = unc(args.path)
    if smbclient.path.isdir(p):
        if not args.recursive:
            print(f'error: {args.path} 是目录，加 --recursive 删除整个目录', file=sys.stderr)
            sys.exit(1)
        rmtree(p)
        print(f'deleted directory tree {args.path}')
    else:
        smbclient.remove(p)
        print(f'deleted {args.path}')


def cmd_move(args):
    smbclient.rename(unc(args.src), unc(args.dst))
    print(f'moved {args.src} -> {args.dst}')


def cmd_read(args):
    with smbclient.open_file(unc(args.path), mode='rb') as f:
        data = f.read(args.bytes) if args.bytes else f.read()
    sys.stdout.write(data.decode('utf-8', 'replace'))


def cmd_find(args):
    pattern = args.name

    def walk(p, rel):
        try:
            entries = list(smbclient.scandir(p))
        except Exception:
            return
        for e in entries:
            r = f'{rel}/{e.name}' if rel else e.name
            if fnmatch.fnmatch(e.name.lower(), pattern.lower()):
                if e.is_dir():
                    print(f'  [DIR]  {r}')
                else:
                    print(f'  {fmt_size(get_size(e)):>9}  {r}')
            if e.is_dir():
                walk(p + '\\' + e.name, r)

    walk(unc(args.path), args.path.strip('\\/') if args.path else '')


def main():
    ensure_config()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('ls');        p.add_argument('path', nargs='?', default='');           p.set_defaults(fn=cmd_ls)
    p = sub.add_parser('tree');      p.add_argument('path', nargs='?', default='');           p.add_argument('--depth', type=int, default=3); p.set_defaults(fn=cmd_tree)
    p = sub.add_parser('stat');      p.add_argument('path');                                   p.set_defaults(fn=cmd_stat)
    p = sub.add_parser('download');  p.add_argument('remote');  p.add_argument('local');       p.set_defaults(fn=cmd_download)
    p = sub.add_parser('upload');    p.add_argument('local');   p.add_argument('remote');      p.set_defaults(fn=cmd_upload)
    p = sub.add_parser('mkdir');     p.add_argument('path');                                   p.set_defaults(fn=cmd_mkdir)
    p = sub.add_parser('delete');    p.add_argument('path');    p.add_argument('--recursive', '--rmrf', action='store_true'); p.set_defaults(fn=cmd_delete)
    p = sub.add_parser('move');      p.add_argument('src');     p.add_argument('dst');         p.set_defaults(fn=cmd_move)
    p = sub.add_parser('read');      p.add_argument('path');    p.add_argument('--bytes', type=int, default=0); p.set_defaults(fn=cmd_read)
    p = sub.add_parser('find');      p.add_argument('path', nargs='?', default='');           p.add_argument('--name', required=True); p.set_defaults(fn=cmd_find)
    p = sub.add_parser('df');                                                                  p.set_defaults(fn=cmd_df)

    args = ap.parse_args()
    smbclient.register_session(SERVER, username=USER, password=PWD)
    try:
        args.fn(args)
    finally:
        try:
            smbclient.reset_connection_cache()
        except Exception:
            pass


if __name__ == '__main__':
    main()
