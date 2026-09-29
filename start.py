# -*- coding: utf-8 -*-
"""
脉衡界 - 启动脚本
负责：检查依赖 → 安装缺失 → 启动Flask服务 → 打开浏览器
"""
import sys
import os
import subprocess
import importlib
import time
import webbrowser
import threading

# 确保Windows控制台使用UTF-8编码，让颜文字正常显示
import io
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 项目路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(SCRIPT_DIR, "backend")
APP_FILE = os.path.join(BACKEND_DIR, "app.py")
REQ_FILE = os.path.join(BACKEND_DIR, "requirements.txt")

# 需要的依赖列表
REQUIRED = [
    ("flask", "flask"),
    ("flask_sqlalchemy", "flask-sqlalchemy"),
    ("flask_cors", "flask-cors"),
    ("dotenv", "python-dotenv"),
    ("requests", "requests"),
    ("openai", "openai"),
    ("PIL", "Pillow"),
    ("cryptography", "cryptography"),
    ("numpy", "numpy"),
    ("httpx", "httpx"),
]

BANNER = """
╔══════════════════════════════════════════╗
  ✿  脉衡界 · 校园健康智能体  ✿
  一键启动器 ٩(◕‿◕)۶
  ─────────────────────────
  你的健康，我来守护 (๑•̀ㅂ•́)و✧
╚══════════════════════════════════════════╗
"""

def check_and_install_deps():
    """检查并安装缺失的依赖"""
    print("[1/3] (｡･ω･｡) 正在检查依赖...")
    missing = []
    for module, package in REQUIRED:
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(package)
    
    if not missing:
        print("  所有依赖已就绪！✧")
        return True
    
    print(f"  发现缺少依赖呢 (´・ω・`): {', '.join(missing)}")
    print("  正在努力安装中... (ง •_•)ง")
    print()
    
    # 用当前Python的pip安装
    result = subprocess.call(
        [sys.executable, "-m", "pip", "install"] + missing,
        cwd=BACKEND_DIR
    )
    
    if result != 0:
        # 如果安装失败，尝试用requirements.txt
        print("  尝试通过requirements.txt安装...")
        result = subprocess.call(
            [sys.executable, "-m", "pip", "install", "-r", REQ_FILE],
            cwd=BACKEND_DIR
        )
    
    if result == 0:
        print()
        print("  依赖安装完成！✧")
        return True
    else:
        print()
        print("  [错误] 啊呀，依赖安装失败了 (；´д｀)")
        print(f"  请手动执行: {sys.executable} -m pip install -r requirements.txt")
        return False

def start_server():
    """启动Flask服务"""
    print("[2/3] 正在启动脉衡界... ε=ε=ε=(~￣▽￣)~")
    print(f"  Python: {sys.executable}")
    print(f"  版本: {sys.version.split()[0]}")
    print(f"  服务地址: http://localhost:5000")
    print()
    
    # 切换工作目录到backend
    os.chdir(BACKEND_DIR)
    
    # 启动Flask
    # 用subprocess启动，这样可以捕获输出
    proc = subprocess.Popen(
        [sys.executable, APP_FILE],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    return proc

def open_browser_delayed():
    """延迟打开浏览器"""
    time.sleep(4)
    try:
        webbrowser.open("http://localhost:5000")
    except:
        pass

def main():
    print(BANNER)
    
    # 检查项目文件
    if not os.path.exists(APP_FILE):
        print(f"[错误] 找不到主程序: {APP_FILE}")
        print("请确保本程序位于项目根目录（与backend文件夹同级）。")
        input("\n按回车键退出...")
        return
    
    print(f"  项目路径: {SCRIPT_DIR}")
    print()
    
    # 1. 检查并安装依赖
    if not check_and_install_deps():
        input("\n按回车键退出...")
        return
    
    print()
    
    # 2. 启动服务
    proc = start_server()
    
    # 3. 延迟打开浏览器
    print("[3/3] 等待服务就绪... (´・ω・`)")
    browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
    browser_thread.start()
    
    # 实时输出Flask日志
    print()
    print("=" * 50)
    print("  脉衡界启动成功！╰(*°▽°*)╯")
    print("  访问地址: http://localhost:5000")
    print("  按Ctrl+C或关闭窗口即可停止服务～")
    print("=" * 50)
    print()
    
    try:
        for line in proc.stdout:
            print("  " + line.rstrip())
    except KeyboardInterrupt:
        print("\n正在停止服务... (´・ω・`)")
        proc.terminate()
        proc.wait()
        print("服务已停止。再见～ (｡･ω･｡)ﾉ")
    
    proc.wait()

if __name__ == "__main__":
    main()
