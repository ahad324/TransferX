import subprocess
import re
import sys

# Configuration
VERSION = "1.0.0"  # Update this for each new release
CLIENT_NAME = "TransferX"
SERVER_NAME = "TransferXServer"
INNO_SETUP_COMPILER = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
SIGNTOOL_PATH = r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe"
CERTIFICATE_PATH = "TransferX_certificate.pfx"
CERTIFICATE_PASSWORD = "ahad324xv"
TIMESTAMP_SERVER = "http://timestamp.digicert.com"

def run_command(command):
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command, stderr.decode())
        return stdout.decode()
    except subprocess.CalledProcessError as e:
        print(f"===========> Error executing command: {command}")
        print(f"===========> Error message: {e.stderr}")
        sys.exit(1)

def build_executable(spec_file, name, dist_dir, build_dir):
    print(f"Building {name}...")
    run_command(f"pyinstaller {spec_file} --distpath {dist_dir} --workpath {build_dir}")

def create_inno_setup(iss_file, name):
    """Creating Inno Setup installer with versioned name."""
    versioned_name = f"{name}_v{VERSION}"
    print(f"Creating Inno Setup installer for {versioned_name}...")
    run_command(f'"{INNO_SETUP_COMPILER}" /F"{versioned_name}" {iss_file}')

def update_version_in_files(file_paths):
    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
                # Update APP_VERSION in .py files
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
        except IOError as e:
            print(f"===========> Error updating file: {file_path}")
            print(f"===========> Error: {str(e)}")
            sys.exit(1)

def sign_executable(exe_path):
    """Sign an executable with the specified certificate."""
    print(f"Signing {exe_path}...")
    sign_command = (
        f'"{SIGNTOOL_PATH}" sign '
        f'/f "{CERTIFICATE_PATH}" '
        f'/p {CERTIFICATE_PASSWORD} '
        f'/tr {TIMESTAMP_SERVER} '
        f'/td SHA256 '
        f'/fd SHA256 '
        f'"{exe_path}"'
    )
    return run_command(sign_command)

def verify_signature(exe_path):
    """Verify that an executable is properly signed."""
    print(f"Verifying signature for {exe_path}...")
    verify_command = f'"{SIGNTOOL_PATH}" verify /pa /v "{exe_path}"'
    try:
        run_command(verify_command)
        print(f"Signature verification successful for {exe_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"===========> Signature verification failed for {exe_path}")
        print(f"===========> Error: {e}")
        return False
    
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

        # Sign the executables
        sign_executable(f"Client/dist/{CLIENT_NAME}.exe")
        sign_executable(f"Server/dist/{SERVER_NAME}.exe")
        
        # Create Inno Setup installers
        create_inno_setup("Client/client.iss", CLIENT_NAME)
        create_inno_setup("Server/server.iss", SERVER_NAME)
        
        # Sign the installers
        sign_executable(f"Client/App/{CLIENT_NAME}_v{VERSION}.exe")
        sign_executable(f"Server/App/{SERVER_NAME}_v{VERSION}.exe")

        # Verify signatures
        executables_to_verify = [
            f"Client/dist/{CLIENT_NAME}.exe",
            f"Server/dist/{SERVER_NAME}.exe",
            f"Client/App/{CLIENT_NAME}_v{VERSION}.exe",
            f"Server/App/{SERVER_NAME}_v{VERSION}.exe"
        ]

        for exe in executables_to_verify:
            if not verify_signature(exe):
                raise Exception(f"Signature verification failed for {exe}")

        print("Build process completed successfully with all signatures verified!")
    except Exception as e:
        print(f"===========> Error during build process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()