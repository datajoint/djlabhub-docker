"""
Return config on servers to start for codeserver

See https://jupyter-server-proxy.readthedocs.io/en/latest/server-process.html
for more information.
"""
import os
import shutil
import subprocess

def setup_codeserver():
    # Make sure codeserver is in $PATH
    def _codeserver_command(port):
        full_path = shutil.which('code-server')
        if not full_path:
            raise FileNotFoundError('Can not find code-server in $PATH')
        working_dir = os.getenv("CODE_WORKINGDIR", None)
        if working_dir is None:
            working_dir = os.getenv("JUPYTER_SERVER_ROOT", ".")

        dj_user = os.getenv("DJ_USER", None)
        dj_user_email = os.getenv("DJ_USER_EMAIL", None)

        # # Run Git commands if user information is provided
        if dj_user and dj_user_email:
            try:
                subprocess.run(['git', 'config', '--global', 'user.name', dj_user], check=True)
                subprocess.run(['git', 'config', '--global', 'user.email', dj_user_email], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error setting Git user: {e}")

        return [full_path, f'--port={port}', "--auth", "none", working_dir]

    return {
        'command': _codeserver_command,
        'timeout': 20,
        'launcher_entry': {
            'title': 'VS Code IDE',
            'icon_path': os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      'icons', 'vscode.svg')
        }
    }