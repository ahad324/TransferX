import os
import subprocess
import hashlib
import json
import shutil
import re
import sys
from datetime import datetime, timezone

# Configuration
VERSION = "0.0.8"  # Update this for each new release
CLIENT_NAME = "TransferX"
SERVER_NAME = "TransferXServer"
INNO_SETUP_COMPILER = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"  # Update this path if necessary
RELEASES_URL = "https://github.com/ahad324/TransferX/releases"
RELEASE_NOTES_URL = f"{RELEASES_URL}/tag/v{VERSION}"
DOWNLOAD_URL_CLIENT = f"{RELEASES_URL}/download/v{VERSION}/TransferX-{VERSION}.exe"
DOWNLOAD_URL_SERVER = f"{RELEASES_URL}/download/v{VERSION}/TransferXServer-{VERSION}.exe"
PUB_DATE = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

def run_command(command):
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command, stderr.decode())
        return stdout.decode()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Error message: {e.stderr}")
        sys.exit(1)

def build_executable(spec_file, name, dist_dir, build_dir):
    print(f"Building {name}...")
    run_command(f"pyinstaller {spec_file} --distpath {dist_dir} --workpath {build_dir}")

def create_inno_setup(iss_file, name):
    print(f"Creating Inno Setup installer for {name}...")
    output = run_command(f'"{INNO_SETUP_COMPILER}" {iss_file}')

def update_version_in_files(file_paths):
    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Update AppVersion in .py files
            if file_path.endswith(".py"):
                match = re.search(r'AppVersion = "([\d.]+)"', content)
                if match:
                    current_version = match.group(1)
                    new_version_line = f'AppVersion = "{VERSION}"'
                    content = content.replace(f'AppVersion = "{current_version}"', new_version_line)
                    print(f"Updated AppVersion in {file_path} from {current_version} to {VERSION}")
                else:
                    print(f"Could not find AppVersion string in {file_path}")
                
            # Update AppVersion in .iss files
            elif file_path.endswith(".iss"):
                version_match = re.search(r'AppVersion = ([\d.]+)', content)
                if version_match:
                    current_version = version_match.group(1)
                    content = content.replace(f'AppVersion = {current_version}', f'AppVersion = {VERSION}')
                    print(f"Updated AppVersion in {file_path} from {current_version} to {VERSION}")
                else:
                    print(f"Could not find AppVersion in {file_path}")
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"Successfully updated {file_path}")
        except IOError as e:
            print(f"Error updating file: {file_path}")
            print(f"Error: {str(e)}")
            sys.exit(1)

def generate_appcast(template_path, output_path, app_name, download_url, executable_path):
    try:
        with open(template_path, "r", encoding="utf-8") as template_file:
            template_content = template_file.read()
        
        appcast_content = template_content.replace("{{APP_NAME}}", app_name)
        appcast_content = appcast_content.replace("{{RELEASES_URL}}", RELEASES_URL)
        appcast_content = appcast_content.replace("{{RELEASE_NOTES_URL}}", RELEASE_NOTES_URL)
        appcast_content = appcast_content.replace("{{VERSION}}", VERSION)
        appcast_content = appcast_content.replace("{{PUB_DATE}}", PUB_DATE)
        appcast_content = appcast_content.replace("{{DOWNLOAD_URL}}", download_url)
        appcast_content = appcast_content.replace("{{FILE_SIZE}}", str(os.path.getsize(executable_path)))

        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(appcast_content)
        
        print(f"Generated {output_path}")
    except IOError as e:
        print(f"Error generating appcast: {output_path}")
        print(f"Error: {str(e)}")
        sys.exit(1)

def main():
    try:
        # Update version in all necessary files
        files_to_update = [
            "Client/updater.py",
            "Server/updater.py",
            "Client/client.iss",
            "Server/server.iss"
        ]
        update_version_in_files(files_to_update)

        # Build executables
        build_executable("Client/client.spec", CLIENT_NAME, "Client/dist", "Client/build")
        build_executable("Server/server.spec", SERVER_NAME, "Server/dist", "Server/build")

        # Copy WinSparkle.dll to dist directories
        shutil.copy("Client/WinSparkle.dll", "Client/dist")
        shutil.copy("Server/WinSparkle.dll", "Server/dist")
        
        # Create Inno Setup installers
        create_inno_setup("Client/client.iss", CLIENT_NAME)
        create_inno_setup("Server/server.iss", SERVER_NAME)

        # Generate appcast.xml files
        generate_appcast("appcast_template.xml", "Client/appcast.xml", CLIENT_NAME, DOWNLOAD_URL_CLIENT, "Client/dist/TransferX.exe")
        generate_appcast("appcast_template.xml", "Server/appcast.xml", SERVER_NAME, DOWNLOAD_URL_SERVER, "Server/dist/TransferXServer.exe")

        print("Build process completed successfully!")
    except Exception as e:
        print(f"Error during build process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()