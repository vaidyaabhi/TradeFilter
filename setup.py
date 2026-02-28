import os
import subprocess
import sys
import platform

def run_cmd(cmd):
    try:
        subprocess.check_call(cmd, shell=True)
    except Exception as e:
        print(f"❌ Error running: {cmd}\n{e}")

def setup():
    print("🚀 Starting TradeFilter Setup...")
    
    # 1. Create Virtual Environment
    if not os.path.exists("venv"):
        py_cmd = "python3.11" if platform.system() == "Darwin" else "python"
        print(f"📦 Creating venv using {py_cmd}...")
        run_cmd(f"{py_cmd} -m venv venv")
    
    # 2. Determine paths based on OS
    if platform.system() == "Windows":
        pip_path = os.path.join("venv", "Scripts", "pip")
        python_path = os.path.join("venv", "Scripts", "python")
    else:
        pip_path = os.path.join("venv", "bin", "pip")
        python_path = os.path.join("venv", "bin", "python")

    # 3. Install Requirements
    print("📥 Installing libraries...")
    run_cmd(f"{pip_path} install --upgrade pip")
    run_cmd(f"{pip_path} install -r requirements.txt")

    # 4. Initialize Database
    if os.path.exists("database.py"):
        print("🗄️ Initializing Database...")
        run_cmd(f"{python_path} database.py")

    print("\n✅ Setup Complete!")
    print(f"👉 To start, activate your venv: {'source venv/bin/activate' if platform.system() != 'Windows' else '.\\venv\\Scripts\\activate'}")

if __name__ == "__main__":
    setup()
