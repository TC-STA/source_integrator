#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
from datetime import datetime
import mimetypes
import chardet  # 需要安装：pip install chardet

# ---------- 默认配置 ----------
# 默认要跳过的文件夹名称
DEFAULT_SKIP_DIRS = {'build', '.git', '__pycache__', 'node_modules', '.gradle', '.idea', 'venv', 'env', 'dist'}

# 默认需要过滤的文件后缀（即使能读成文本也强制跳过）
DEFAULT_EXCLUDE_EXT = {
    # 常见二进制/多媒体
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
def check_and_install(package):
    try:
        __import__(package)
    except ImportError:
        print(f"缺少依赖库 '{package}'，正在尝试自动安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

check_and_install("chardet")

# ---------- 工具函数 ----------
def is_binary_file(file_path: Path, sample_size: int = 1024) -> bool:
    """
    通过读取文件头部判断是否为二进制文件。
    如果包含空字节或不可打印字符比例过高，则视为二进制。
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(sample_size)
            if not chunk:
                return False  # 空文件视为文本
            # 检测空字节
            if b'\x00' in chunk:
                return True
            # 使用 chardet 检测编码置信度
            detect_result = chardet.detect(chunk)
            confidence = detect_result.get('confidence', 0)
            # 如果置信度极低，可能不是文本
            if confidence < 0.5:
                return True
            # 尝试解码
            encoding = detect_result.get('encoding', 'utf-8')
            chunk.decode(encoding, errors='strict')
            return False
    except (UnicodeDecodeError, LookupError, TypeError):
        return True
    except Exception:
        return True


def read_file_content(file_path: Path) -> str:
    """读取文件内容，自动检测编码。二进制文件会抛出异常由上层处理。"""
    with open(file_path, 'rb') as f:
        raw = f.read()
        if not raw:
            return ""
        # 使用 chardet 检测编码
        encoding = chardet.detect(raw).get('encoding', 'utf-8')
        return raw.decode(encoding, errors='replace')


def get_file_size_str(size_bytes: int) -> str:
    """字节转可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def generate_tree(dir_path: Path, prefix: str = "", skip_dirs: set = None) -> list:
    """递归生成目录树形结构字符串列表"""
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
    print("="*80)
    print("By TC_STA")
    print("1.0")
    print("="*80)
    print("""
源码文件整合工具（支持所有文件类型）
功能：
1. 生成项目文件夹树形结构
2. 智能读取所有文件内容（文本文件显示内容，二进制文件仅显示 [二进制文件，跳过内容]）
3. 输出文件大小排行榜
4. 支持屏蔽 build 等文件夹
5. 支持自定义过滤文件后缀
选项:
    0. 退出
""")

def main():
    print("=" * 80)

    # 1. 获取源码文件夹路径
    src_path = input("请输入源码文件夹路径（可直接粘贴）: ").strip()
    if src_path == "0":
            print("程序已退出")
            return 0
    if src_path.startswith(('"', "'")) and src_path.endswith(('"', "'")):
        src_path = src_path[1:-1]
    src_dir = Path(src_path).resolve()
    if not src_dir.exists() or not src_dir.is_dir():
        print(f"错误：路径不存在或不是文件夹 -> {src_dir}")
        sys.exit(1)

    # 2. 是否屏蔽 build 文件夹
    skip_build = input("是否屏蔽 build 文件夹？(y/n，默认 y): ").strip().lower() != 'n'
    skip_dirs = set(DEFAULT_SKIP_DIRS)
    if not skip_build:
        skip_dirs.discard('build')

    # 3. 自定义过滤后缀
    exclude_ext = set(DEFAULT_EXCLUDE_EXT)
    print("\n当前默认过滤的后缀（可修改）:")
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

    # 4. 是否自定义包含后缀（如果不想用智能检测，可强制指定后缀，这里我们默认智能检测，所以留空）
    print("\n注意：本工具将智能检测所有文件内容，二进制文件只显示文件名。")

    input("\n按回车开始整合...")

    # 收集所有文件的路径和大小
    file_info_list = []  # (relative_path, file_path, size_bytes)

    print("正在扫描文件夹...")
    for root, dirs, files in os.walk(src_dir):
        # 过滤要跳过的目录
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        root_path = Path(root)
        for file in files:
            file_path = root_path / file
            # 后缀过滤检查
            if file_path.suffix.lower() in exclude_ext:
                continue
            size = file_path.stat().st_size
            rel_path = file_path.relative_to(src_dir)
            file_info_list.append((rel_path, file_path, size))

    print(f"共找到 {len(file_info_list)} 个文件。")

    # 按文件大小排序（用于排行榜）
    sorted_by_size = sorted(file_info_list, key=lambda x: x[2], reverse=True)

    # 生成输出文件路径
    output_file = src_dir / "整合文件.txt"

    # 开始写入
    print("正在生成整合文件...")
    with open(output_file, 'w', encoding='utf-8') as out:
        # 头部信息
        out.write("=" * 80 + "\n")
        out.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out.write(f"源码文件夹: {src_dir}\n")
        out.write(f"文件总数: {len(file_info_list)}\n")
        out.write("=" * 80 + "\n\n")

        # 1. 项目树形结构
        out.write("【项目树形结构】\n")
        out.write("=" * 80 + "\n")
        tree_lines = generate_tree(src_dir, skip_dirs=skip_dirs)
        out.write("\n".join(tree_lines))
        out.write("\n\n")

        # 2. 所有文件内容
        out.write("【文件内容】\n")
        out.write("=" * 80 + "\n")
        for rel_path, abs_path, size in sorted(file_info_list, key=lambda x: str(x[0]).lower()):
            out.write(f"\n{'─' * 80}\n")
            out.write(f"文件路径: {rel_path}\n")
            out.write(f"文件大小: {get_file_size_str(size)}\n")
            out.write(f"{'─' * 80}\n")
            # 检查是否为二进制文件
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

        # 3. 文件大小排行榜
        out.write("【文件大小排行榜 (Top 50)】\n")
        out.write("=" * 80 + "\n")
        out.write(f"{'排名':<6}{'大小':<15}{'路径'}\n")
        out.write("-" * 80 + "\n")
        for idx, (rel_path, _, size) in enumerate(sorted_by_size[:50], 1):
            out.write(f"{idx:<6}{get_file_size_str(size):<15}{rel_path}\n")
        out.write("\n")
        out.write("=" * 80 + "\n")
        out.write("整合完成！\n")

    print(f"\n✅ 整合成功！文件已生成：\n{output_file}")
    print("按回车退出...")
    input()


if __name__ == "__main__":
    Introducing_the_usage_of_the_program()
    main()
