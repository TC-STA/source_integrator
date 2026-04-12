#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import urllib.request
import ssl
from pathlib import Path
from datetime import datetime

LOCAL_VERSION = "1.10"          # 版本
VERSION_CHECK_URL = "https://gist.githubusercontent.com/TC-STA/51746f15c16389c34b871e0c95672411/raw/a671a76478cdf1cd23cebee8c20d8fa3b2aa49f2/version.txt"   

UPDATE_DOWNLOAD_URL = "https://github.com/TC-STA/source_integrator/releases" #下载地址

# 默认要跳过的文件夹
DEFAULT_SKIP_DIRS = {'build', '.git', '__pycache__', 'node_modules', '.gradle', '.idea', 'venv', 'env', 'dist'}

# 默认要过滤的文件后缀（不会读取内容）
DEFAULT_EXCLUDE_EXT = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp', '.svg',
    '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac', '.mkv', '.ogg', '.wmv',
    '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar', '.xz',
    '.exe', '.dll', '.so', '.dylib', '.bin', '.apk', '.ipa', '.app', '.msi',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.pyc', '.pyo', '.class', '.o', '.obj', '.lib', '.a',
    '.db', '.sqlite', '.sqlite3',
    '.ttf', '.otf', '.woff', '.woff2',
    '.pkl', '.pickle', '.joblib',
    '.npy', '.npz',
}

# ---------- 版本检测函数（自动运行） ----------
def check_update():
    """启动时联网检测是否有新版本，如果有就打印提示，没有或网络不通就静默跳过"""
    try:
        # 创建不验证SSL证书的上下文
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(VERSION_CHECK_URL, timeout=5, context=ctx) as resp:
            remote_version = resp.read().decode('utf-8').strip()
        # 比较版本号
        if remote_version > LOCAL_VERSION:
            print("\n" + "=" * 60)
            print(f"🔔 发现新版本：{remote_version}（当前版本：{LOCAL_VERSION}）")
            print(f"请前往下载：{UPDATE_DOWNLOAD_URL}")
            print("=" * 60 + "\n")
    except Exception:
        # 任何错误都静默跳过，不影响正常使用
        pass

# ---------- 以下是原有的整合功能  ----------
def is_binary_file(file_path: Path, sample_size: int = 1024) -> bool:
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(sample_size)
            if not chunk:
                return False
            if b'\x00' in chunk:
                return True
            for encoding in ('utf-8', 'gbk', 'latin-1'):
                try:
                    chunk.decode(encoding)
                    return False
                except UnicodeDecodeError:
                    continue
            return True
    except Exception:
        return True

def read_file_content(file_path: Path) -> str:
    with open(file_path, 'rb') as f:
        raw = f.read()
        if not raw:
            return ""
        for encoding in ('utf-8', 'gbk', 'latin-1'):
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                continue
        return raw.decode('utf-8', errors='replace')

def get_file_size_str(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def generate_tree(dir_path: Path, prefix: str = "", skip_dirs: set = None) -> list:
    if skip_dirs is None:
        skip_dirs = set()
    lines = []
    try:
        items = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return [f"{prefix}[权限不足]"]
    for i, item in enumerate(items):
        is_last = (i == len(items) - 1)
        connector = '└── ' if is_last else '├── '
        if item.is_dir():
            if item.name in skip_dirs:
                lines.append(f"{prefix}{connector}{item.name}/ (已屏蔽)")
                continue
            lines.append(f"{prefix}{connector}{item.name}/")
            extension = "    " if is_last else "│   "
            lines.extend(generate_tree(item, prefix + extension, skip_dirs))
        else:
            lines.append(f"{prefix}{connector}{item.name}")
    return lines

def Introducing_the_usage_of_the_program():
    print("=" * 80)
    print("源码文件整合工具 (By TC_STA) 版本", LOCAL_VERSION)
    print("=" * 80)
    print("""
功能：
1. 生成项目文件夹树形结构
2. 智能读取所有文件内容（文本显示，二进制仅显示文件名）
3. 输出文件大小排行榜
4. 支持屏蔽 build 等文件夹
5. 支持自定义过滤文件后缀
选项: 输入 0 退出
""")

def main():
    print("=" * 80)
    src_path = input("请输入源码文件夹路径（可直接粘贴，输入 0 退出）: ").strip()
    if src_path == "0":
        print("程序已退出")
        sys.exit(0)
    if src_path.startswith(('"', "'")) and src_path.endswith(('"', "'")):
        src_path = src_path[1:-1]
    src_dir = Path(src_path).resolve()
    if not src_dir.exists() or not src_dir.is_dir():
        print(f"错误：路径不存在或不是文件夹 -> {src_dir}")
        sys.exit(1)

    skip_build = input("是否屏蔽 build 文件夹？(y/n，默认 y): ").strip().lower() != 'n'
    skip_dirs = set(DEFAULT_SKIP_DIRS)
    if not skip_build:
        skip_dirs.discard('build')

    exclude_ext = set(DEFAULT_EXCLUDE_EXT)
    print("\n当前默认过滤的后缀:")
    print(", ".join(sorted(exclude_ext)) if exclude_ext else "无")
    custom_choice = input("是否添加额外过滤后缀？(y/n): ").strip().lower()
    if custom_choice == 'y':
        new_ext = input("请输入要过滤的后缀，用逗号分隔（例如 .log,.tmp）: ").strip()
        if new_ext:
            for ext in new_ext.split(','):
                ext = ext.strip()
                if ext and not ext.startswith('.'):
                    ext = '.' + ext
                if ext:
                    exclude_ext.add(ext.lower())
    print(f"\n最终过滤后缀: {', '.join(sorted(exclude_ext)) if exclude_ext else '无'}")
    print("\n注意：本工具将智能检测所有文件内容，二进制文件只显示文件名。")
    input("\n按回车开始整合...")

    file_info_list = []
    print("正在扫描文件夹...")
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        root_path = Path(root)
        for file in files:
            file_path = root_path / file
            if file_path.suffix.lower() in exclude_ext:
                continue
            size = file_path.stat().st_size
            rel_path = file_path.relative_to(src_dir)
            file_info_list.append((rel_path, file_path, size))

    print(f"共找到 {len(file_info_list)} 个文件。")
    sorted_by_size = sorted(file_info_list, key=lambda x: x[2], reverse=True)
    output_file = src_dir / "整合文件.txt"

    print("正在生成整合文件...")
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write("=" * 80 + "\n")
        out.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out.write(f"源码文件夹: {src_dir}\n")
        out.write(f"文件总数: {len(file_info_list)}\n")
        out.write("=" * 80 + "\n\n")

        out.write("【项目树形结构】\n")
        out.write("=" * 80 + "\n")
        tree_lines = generate_tree(src_dir, skip_dirs=skip_dirs)
        out.write("\n".join(tree_lines))
        out.write("\n\n")

        out.write("【文件内容】\n")
        out.write("=" * 80 + "\n")
        for rel_path, abs_path, size in sorted(file_info_list, key=lambda x: str(x[0]).lower()):
            out.write(f"\n{'─' * 80}\n")
            out.write(f"文件路径: {rel_path}\n")
            out.write(f"文件大小: {get_file_size_str(size)}\n")
            out.write(f"{'─' * 80}\n")
            if is_binary_file(abs_path):
                out.write("[二进制文件，跳过内容显示]\n")
            else:
                try:
                    content = read_file_content(abs_path)
                    out.write(content)
                    if not content.endswith('\n'):
                        out.write('\n')
                except Exception as e:
                    out.write(f"[读取失败: {e}]\n")
            out.write("\n")

        out.write("【文件大小排行榜 (Top 50)】\n")
        out.write("=" * 80 + "\n")
        out.write(f"{'排名':<6}{'大小':<15}{'路径'}\n")
        out.write("-" * 80 + "\n")
        for idx, (rel_path, _, size) in enumerate(sorted_by_size[:50], 1):
            out.write(f"{idx:<6}{get_file_size_str(size):<15}{rel_path}\n")
        out.write("\n" + "=" * 80 + "\n整合完成！\n")

    print(f"\n✅ 整合成功！文件已生成：\n{output_file}")
    input("按回车退出...")

def clear_screen():
    if sys.platform == 'win32':
        os.system('cls')
    else:
        os.system('clear')

if __name__ == "__main__":
    # 启动时检测更新
    check_update()
    while True:
        Introducing_the_usage_of_the_program()
        main()
        clear_screen()