"""
Galgame Studio - 启动入口
双击运行，自动打开浏览器
"""

import os
import sys
import webbrowser
import threading
import time

def main():
    print("=" * 50)
    print("  [Galgame Studio v0.2.1]")
    print("  Novel -> Script -> Prompts -> Pack")
    print("=" * 50)
    
    # 获取脚本所在目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    from server import start_server
    
    host = "127.0.0.1"
    port = 8888
    
    # 启动服务器的线程
    def run_server():
        start_server(host, port)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # 等待服务器启动
    time.sleep(1.5)
    
    url = f"http://{host}:{port}"
    print(f"\n[OK] Server: {url}")
    print("[!] Browser should open automatically")
    print("[X] Close this window to stop\n")
    
    # 打开浏览器
    webbrowser.open(url)
    
    # 保持主线程存活
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[BYE] Goodbye!")


if __name__ == "__main__":
    main()
