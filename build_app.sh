#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔨 开始构建 JazzKeys.app..."

cd "$PROJECT_DIR"

# 清理旧的构建产物
rm -rf build dist

# 构建
python3 setup.py py2app

echo ""
echo "✅ 构建完成！正在测试启动..."
echo ""

# 复制到项目根目录
rm -rf JazzKeys.app
cp -r dist/JazzKeys.app ./JazzKeys.app

# 测试启动（直接在终端运行可以看到报错）
echo "🎹 启动 JazzKeys... (按 Ctrl+C 退出)"
"./JazzKeys.app/Contents/MacOS/JazzKeys"
