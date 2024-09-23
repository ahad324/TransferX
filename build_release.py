import os
import subprocess
import hashlib
import json
import shutil
import re
import sys

# Configuration
VERSION = "0.0.7"  # Update this for each new release
CLIENT_NAME = "TransferX"
SERVER_NAME = "TransferXServer"
INNO_SETUP_COMPILER = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"  # Update this path if necessary

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

def update_version_in_files():
    files_to_update = [
        "Client/updater.py",
        "Server/updater.py"
    ]
    for file_path in files_to_update:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            match = re.search(r'CURRENT_VERSION = "([\d.]+)"', content)
            if match:
                current_version = match.group(1)
                new_version_line = f'CURRENT_VERSION = "{VERSION}"'
                content = content.replace(f'CURRENT_VERSION = "{current_version}"', new_version_line)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                print(f"Updated version in {file_path} from {current_version}-> {VERSION}")
            else:
                print(f"Could not find version string in {file_path}")
        except IOError as e:
            print(f"Error updating version in file: {file_path}")
            print(f"Error: {str(e)}")
            sys.exit(1)

def update_iss_file(file_path, app_name, output_base_filename):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Update AppVersion
        version_match = re.search(r'AppVersion=([\d.]+)', content)
        if version_match:
            current_version = version_match.group(1)
            content = content.replace(f'AppVersion={current_version}', f'AppVersion={VERSION}')
            print(f"Updated AppVersion in {file_path} from {current_version}-> {VERSION}")
        else:
            print(f"Could not find AppVersion in {file_path}")
        
        # Update OutputBaseFilename
        filename_match = re.search(r'OutputBaseFilename=([\w-]+v[\d.]+)', content)
        if filename_match:
            current_filename = filename_match.group(1)
            new_filename = f"{app_name}-v{VERSION}"
            content = content.replace(f'OutputBaseFilename={current_filename}', f'OutputBaseFilename={new_filename}')
            print(f"OutputBaseFilename in {file_path} from {current_filename}-> {new_filename}")
        else:
            print(f"Could not find OutputBaseFilename in {file_path}")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Successfully updated {file_path}")
    except IOError as e:
        print(f"Error updating .iss file: {file_path}")
        print(f"Error: {str(e)}")
        sys.exit(1)

def main():
    try:
        # Update version in all necessary files
        update_version_in_files()

        # Update .iss files
        update_iss_file("Client/client.iss", "TransferX", f"{CLIENT_NAME}-v{VERSION}")
        update_iss_file("Server/server.iss", "TransferXServer", f"{SERVER_NAME}-v{VERSION}")

        # Build executables
        build_executable("Client/client.spec", CLIENT_NAME, "Client/dist", "Client/build")
        build_executable("Server/server.spec", SERVER_NAME, "Server/dist", "Server/build")

        # Create Inno Setup installers
        create_inno_setup("Client/client.iss", CLIENT_NAME)
        create_inno_setup("Server/server.iss", SERVER_NAME)

        client_installer = f"Client/App/{CLIENT_NAME}-v{VERSION}.exe"
        server_installer = f"Server/App/{SERVER_NAME}-v{VERSION}.exe"

        # Debugging information
        print(f"Expected client installer path: {client_installer}")
        print(f"Expected server installer path: {server_installer}")

        if not os.path.exists(client_installer):
            raise FileNotFoundError(f"Client installer not found: {client_installer}")
        if not os.path.exists(server_installer):
            raise FileNotFoundError(f"Server installer not found: {server_installer}")

        print("Build process completed successfully!")
        print("Don't forget to update the version.json file on your server!")
    except Exception as e:
        print(f"Error during build process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()