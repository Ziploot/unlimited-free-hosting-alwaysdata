import os
import sys
import time

# 1. Failsafe Paramiko Installation
try:
    import paramiko
except ImportError:
    print("[INFO] Paramiko SSH library not found. Installing via pip...")
    import subprocess
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "paramiko"], check=True)
        import paramiko
        print("[SUCCESS] Paramiko installed successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to install paramiko automatically: {e}")
        print("Please run: pip install paramiko")
        sys.exit(1)

def sftp_upload_dir(sftp, local_dir, remote_dir):
    # Recursively create remote folders and upload files
    try:
        sftp.mkdir(remote_dir)
    except IOError:
        pass # Directory already exists
        
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = remote_dir + "/" + item
        
        if os.path.isdir(local_path):
            sftp_upload_dir(sftp, local_path, remote_path)
        else:
            print(f"Uploading: {item} -> {remote_path}")
            sftp.put(local_path, remote_path)

def main():
    print("==============================================")
    print("   ⚡ ZIPLOOT ALWAYSDATA AUTOMATED DEPLOYER")
    print("==============================================")
    print("   Node.js + Databases + 1GB Free Storage")
    print("==============================================")
    print()

    # Get user inputs
    host = input("[INPUT] SSH Host (e.g. ssh-ziploot.alwaysdata.net): ").strip()
    username = input("[INPUT] SSH Username (e.g. ziploot): ").strip()
    password = input("[INPUT] SSH Password: ").strip()
    site_domain = input(f"[INPUT] Your Website Domain (e.g. ziploot.alwaysdata.net): ").strip()

    if not host or not username or not password or not site_domain:
        print("[ERROR] All inputs are required!")
        sys.exit(1)

    print()
    print("[INFO] Connecting to Alwaysdata via SSH...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(host, username=username, password=password, timeout=15)
        print("[SUCCESS] Connected to SSH server successfully!")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(1)

    # 1. Define Paths
    # Alwaysdata standard paths for website directories is /home/username/www or custom subfolders
    # The default site path is typically /home/username/www
    remote_dir = f"/home/{username}/www"
    print(f"[INFO] Deploying application to folder: {remote_dir}")

    # 2. Upload project files via SFTP
    print()
    print("[INFO] Uploading files to Alwaysdata...")
    sftp = ssh.open_sftp()
    
    local_app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")
    if not os.path.exists(local_app_dir):
        print(f"[ERROR] Local app folder not found at: {local_app_dir}")
        sftp.close()
        ssh.close()
        sys.exit(1)
        
    try:
        sftp_upload_dir(sftp, local_app_dir, remote_dir)
        print("[SUCCESS] All files uploaded successfully!")
    except Exception as e:
        print(f"[ERROR] SFTP Upload failed: {e}")
        sftp.close()
        ssh.close()
        sys.exit(1)
    finally:
        sftp.close()

    # 3. Install NPM dependencies on Alwaysdata
    print()
    print("[INFO] Installing npm dependencies on Alwaysdata...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {remote_dir} && npm install")
    npm_out = stdout.read().decode('utf-8', errors='ignore')
    npm_err = stderr.read().decode('utf-8', errors='ignore')
    
    print("[INFO] npm install log:")
    print(npm_out)
    if npm_err:
        print(npm_err)

    # 4. Trigger Passenger Restart
    # Alwaysdata runs websites using Phusion Passenger. 
    # To restart Passenger apps, we touch tmp/restart.txt
    print()
    print("[INFO] Triggering Passenger Node.js app restart...")
    ssh.exec_command(f"mkdir -p {remote_dir}/tmp && touch {remote_dir}/tmp/restart.txt")
    print("[SUCCESS] Touch tmp/restart.txt triggered successfully!")

    print()
    print("==============================================")
    print("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
    print("==============================================")
    print(f"🔗 Live Website: http://{site_domain}")
    print("==============================================")
    print()
    
    ssh.close()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
