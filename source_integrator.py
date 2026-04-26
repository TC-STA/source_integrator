#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TC_STA

import os
import sys
import urllib.request
import urllib.error
import ssl
import time
import shutil
import tempfile
import zipfile
import io
from pathlib import Path
from datetime import datetime

LOCAL_VERSION = "2.1.0"          # 版本更新
VERSION_CHECK_URL = "https://gitee.com/TC_STA/version/raw/master/version.txt"
UPDATE_DOWNLOAD_URL = "https://github.com/TC-STA/source_integrator/releases"

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

def clear_screen():
    if sys.platform == 'win32':
        os.system('cls')
    else:
        os.system('clear')

# ---------- 版本检测 ----------
def check_update():
    """启动时联网检测是否有新版本"""
    if sys.platform.startswith('win'):
        os.system("")  # 启用 ANSI 颜色支持
    try:
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(VERSION_CHECK_URL, timeout=5, context=ctx) as resp:
            remote_version = resp.read().decode('utf-8').strip()
        print("\033[33m香香软软的管理员:\033[0m" + "\033[96;40m正在检测是否有新版本...\033[0m")
        time.sleep(2)
        if remote_version == LOCAL_VERSION:
            print("\033[33m香香软软的管理员:\033[0m" + "\033[96;40m暂无发现新版本ε٩(๑> ₃ <)۶з\033[0m")
            time.sleep(2)
            clear_screen()
            return
        if remote_version > LOCAL_VERSION:
            print("\n" + "=" * 60)
            print("\033[33m香香软软的管理员:\033[0m" + "快去给我下" + "\033[31m杂鱼(｡•ˇ‸ˇ•｡)\033[0m")
            print(f"🔔 发现新版本：{remote_version}（当前版本：{LOCAL_VERSION}）")
            print(f"请前往下载：{UPDATE_DOWNLOAD_URL}")
            print("=" * 60 + "\n")
    except Exception:
        pass

# ---------- 工具函数 ----------
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

def parse_github_url(url: str) -> tuple:
    """
    解析 GitHub URL，返回 (owner, repo, branch)。
    支持格式：
        https://github.com/owner/repo
        https://github.com/owner/repo.git
        https://github.com/owner/repo/tree/branch
    如果未指定分支，默认使用 'main'。
    """
    url = url.rstrip('/').rstrip('.git')
    parts = url.split('/')
    if 'github.com' not in parts:
        raise ValueError("不是有效的 GitHub URL")
    try:
        idx = parts.index('github.com')
        owner = parts[idx + 1]
        repo = parts[idx + 2]
        branch = 'main'  # 默认分支
        if len(parts) > idx + 3 and parts[idx + 3] == 'tree':
            branch = '/'.join(parts[idx + 4:])  # 可能嵌套路径
        return owner, repo, branch
    except (ValueError, IndexError):
        raise ValueError("GitHub URL 格式错误，应为 https://github.com/owner/repo")

def download_with_progress(url: str, dest_path: str):
    """下载文件并显示简易进度条"""
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(url, context=ctx) as response:
        total = int(response.getheader('Content-Length', 0))
        block_size = 8192
        downloaded = 0
        print(f"开始下载（{get_file_size_str(total) if total else '未知大小'}）...")
        with open(dest_path, 'wb') as f:
            while True:
                chunk = response.read(block_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    percent = downloaded * 100 // total
                    bar_len = 40
                    filled = int(bar_len * percent / 100)
                    bar = '█' * filled + '░' * (bar_len - filled)
                    print(f"\r进度: |{bar}| {percent:3d}%", end='', flush=True)
        print()  # 换行

def download_and_extract_github_repo(url: str, temp_dir: str) -> Path:
    """
    下载并解压 GitHub 仓库，返回解压后的根目录路径。
    """
    owner, repo, branch = parse_github_url(url)
    zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
    zip_file = os.path.join(temp_dir, f"{repo}.zip")
    print(f"正在下载 {owner}/{repo} 的 {branch} 分支...")
    download_with_progress(zip_url, zip_file)
    print("下载完成，正在解压...")
    with zipfile.ZipFile(zip_file, 'r') as zf:
        zf.extractall(temp_dir)
    # 解压后通常是一个 {repo}-{branch} 目录
    extracted_name = f"{repo}-{branch}"
    extracted_path = os.path.join(temp_dir, extracted_name)
    if not os.path.isdir(extracted_path):
        # 尝试查找第一个子目录
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isdir(item_path):
                extracted_path = item_path
                break
    return Path(extracted_path)

# ---------- 使用说明 ----------
def print_intro():
    print("=" * 80)
    print(f"源码文件整合工具 (By TC_STA)  版本 {LOCAL_VERSION}")
    print("=" * 80)
    print("""
【功能说明】
  本工具可将整个项目源码（本地或 GitHub 远程仓库）整合为一个文本文件，
  方便输入给大语言模型（如 ChatGPT）进行代码分析或问答。

  ✨ 新功能：支持直接输入 GitHub 仓库链接，自动下载并整合！
  
【使用方式】
  1. 输入本地文件夹路径 → 分析本地项目
  2. 输入 GitHub 仓库链接 → 自动下载、解压并分析
     格式示例：
       • https://github.com/owner/repo
       • https://github.com/owner/repo/tree/main
  3. 屏蔽文件夹：默认屏蔽 build、.git 等，可按需调整
  4. 过滤文件后缀：图片、音频、二进制等默认不读取内容
  5. 生成文件：在源码目录（或临时目录）生成「整合文件.txt」
  
【注意事项】
  - GitHub 仓库下载需要网络，较大仓库可能耗时。
  - 解压后的临时文件默认不自动删除，整合完成后会提示是否清理。
  - 输入 0 可随时退出。
""")
#qtmdlswl
def main():
    print("=" * 80)
    src_input = input("请输入源码文件夹路径 或 GitHub 仓库链接 (输入 0 退出): ").strip()
    if src_input == "0":
        print("程序已退出")
        sys.exit(0)

    # 去除首尾引号
    if src_input.startswith(('"', "'")) and src_input.endswith(('"', "'")):
        src_input = src_input[1:-1]

    # 判断是 GitHub URL 还是本地路径
    is_github = 'github.com' in src_input
    temp_dir = None
    src_dir = None

    if is_github:
        temp_dir = tempfile.mkdtemp(prefix="source_integrator_")
        try:
            src_dir = download_and_extract_github_repo(src_input, temp_dir)
        except Exception as e:
            print(f"错误：下载或解析 GitHub 仓库失败 - {e}")
            sys.exit(1)
    else:
        src_dir = Path(src_input).resolve()
        if not src_dir.exists() or not src_dir.is_dir():
            print(f"错误：路径不存在或不是文件夹 -> {src_dir}")
            sys.exit(1)

    # 后续配置
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

    # 扫描文件
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

    # 如果是 GitHub 下载，询问是否清理临时文件
    if temp_dir and os.path.isdir(temp_dir):
        clean = input("\n是否删除下载的临时文件？(y/n，默认 y): ").strip().lower() != 'n'
        if clean:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print("临时文件已清理。")
        else:
            print(f"临时文件保留在：{temp_dir}")

    input("按回车退出...")

if __name__ == "__main__":
    clear_screen()
    check_update()

    while True:
        print_intro()
        main()
        clear_screen()
