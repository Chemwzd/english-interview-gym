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
  echo "⚠️  程序文件不完整：_internal/Python 缺失。"
  echo ""
  echo "常见原因：macOS 安全弹窗（“已损坏…应移到废纸篓”）删除了文件，或解压不完整。"
  echo "处理步骤："
  echo "   ① 重要：若弹出“已损坏/移到废纸篓”一类对话框，请点【取消】，不要点“移到废纸篓”；"
  echo "   ② 删除当前文件夹，重新解压（建议访达双击 zip，或终端：ditto -x -k 安装包.zip .）；"
  echo "   ③ 再双击本脚本启动（会自动去除隔离标记，无需其他操作）。"
  echo ""
  read -r -p "按回车键退出…" _
  exit 1
fi

exec ./EnglishInterviewGym
