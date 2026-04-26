# 源码文件整合工具 (Source Integrator by TC_STA) 使用说明

**作者**：TC_STA  
**适用平台**：Windows / Linux / macOS（Python 3 环境）

## 功能简介

本工具可以将一个完整的项目源码（本地或远程 GitHub 仓库）整合为一个结构清晰的文本文件 (`整合文件.txt`)。  
整合后的文件包含：

- 项目树形结构
- 所有文本文件的内容（二进制文件仅列出文件名）
- 文件大小排行榜（Top 50）

非常适合将代码喂给大语言模型（如 ChatGPT）进行分析、问答或代码审查。

---

## ✨ 新功能：支持 GitHub 远程仓库

除了分析本地文件夹外，**现在可以直接输入 GitHub 仓库链接**，工具会自动下载、解压并整合整个源码！

### 支持的链接格式

- `https://github.com/owner/repo`
- `https://github.com/owner/repo.git`
- `https://github.com/owner/repo/tree/branch` （指定分支）

工具默认拉取 `main` 分支，若链接中指定了分支则使用指定分支。

---

## 🚀 快速开始

### 1. 安装依赖

该工具仅使用 Python 标准库，无需额外安装第三方包。  
确保系统已安装 **Python 3.6 或以上** 即可。

### 2. 运行方式

```bash
python source_integrator.py
