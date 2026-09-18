#!/bin/bash
# 双击本文件 = 启动「英语面试健身房」（本地服务；关闭本终端窗口即退出）
cd "$(dirname "$0")" || exit 1

# 1) 去除"隔离"标记：浏览器下载的文件会带 com.apple.quarantine，
#    macOS（尤其 26+）会对未签名应用拦截加载内嵌动态库（报 "library load disallowed by system policy"）。
xattr -dr com.apple.quarantine "$(pwd)" 2>/dev/null || true

# 2) 完整性自检：部分第三方解压工具（如 The Unarchiver）会漏掉 .framework 目录，
#    导致 _internal/Python 指向不存在的目标，启动时报 "Failed to load Python shared library"。
if ! [ -e "_internal/Python" ]; then
  echo ""
  echo "⚠️  程序文件不完整：_internal/Python 缺失或链接无效。"
  echo ""
  echo "常见原因：用第三方解压工具解压时漏掉了 .framework 目录。"
  echo "请改用以下任一方式【重新解压】（先删除当前文件夹）："
  echo "   · 访达里直接双击 zip —— 用系统自带解压；"
  echo "   · 或终端执行：  ditto -x -k 你的安装包.zip ."
  echo ""
  read -r -p "按回车键退出…" _
  exit 1
fi

exec ./EnglishInterviewGym
