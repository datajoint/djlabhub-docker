import os
import pwd
import hashlib
import random
import json

# Configuration file for jupyter-server.

# c = get_config()  # noqa
from traitlets.config import Config

c = Config() if "c" not in locals() else c

# get the current user
user = [u for u in pwd.getpwall() if u.pw_uid == os.getuid()][0]

## Whether to allow the user to run the server as root.
#  Default: False
c.ServerApp.allow_root = False

## The IP address the Jupyter server will listen on.
#  Default: 'localhost'
c.ServerApp.ip = os.getenv("JUPYTER_SERVER_APP_IP", "0.0.0.0")


## DEPRECATED in 2.0. Use PasswordIdentityProvider.hashed_password
#  Default: ''
# c.ServerApp.password = ''
def passwd(passphrase: str):
    salt_len = 12
    h = hashlib.new("sha256")
    salt = ("%0" + str(salt_len) + "x") % random.getrandbits(4 * salt_len)
    h.update(passphrase.encode("utf-8") + salt.encode("ascii"))
    return ":".join(("sha256", salt, h.hexdigest()))


jupyter_server_password = os.getenv("JUPYTER_SERVER_APP_PASSWORD", "datajoint")
c.PasswordIdentityProvider.hashed_password = (
    passwd(jupyter_server_password) if jupyter_server_password else ""
)

## The port the server will listen on (env: JUPYTER_PORT).
#  Default: 0
c.ServerApp.port = int(os.getenv("JUPYTER_SERVER_APP_PORT", 8888))

## The directory to use for notebooks and kernels.
#  Default: ''
c.ServerApp.root_dir = os.getenv("JUPYTER_SERVER_APP_ROOT_DIR", user.pw_dir)

## Supply overrides for terminado. Currently only supports "shell_command".
#  Default: {}
c.ServerApp.terminado_settings = json.loads(
    os.getenv(
        "JUPYTER_SERVER_APP_TERMINADO_SETTINGS",
        f'{{"shell_command": ["{user.pw_shell}"]}}',
    )
)


## Python callable or importstring thereof
#  See also: ContentsManager.pre_save_hook
# c.FileContentsManager.pre_save_hook = None
def scrub_output_pre_save(model, **kwargs):
    """scrub output before saving notebooks"""
    if not os.getenv("JUPYTER_FILE_CONTENTS_MANAGER_SAVE_OUTPUT", "FALSE") == "TRUE":
        # only run on notebooks
        if model["type"] != "notebook":
            return
        # only run on nbformat v4
        if model["content"]["nbformat"] != 4:
            return

        model["content"]["metadata"].pop("signature", None)
        for cell in model["content"]["cells"]:
            if cell["cell_type"] != "code":
                continue
            cell["outputs"] = []
            cell["execution_count"] = None
    else:
        return


c.FileContentsManager.pre_save_hook = scrub_output_pre_save


#  Default: ''
c.FileContentsManager.root_dir = os.getenv(
    "JUPYTER_FILE_CONTENTS_MANAGER_ROOT_DIR", "/home/jovyan"
)

## Jupyter collaboration extension
c.YDocExtension.disable_rtc = (
    os.getenv("JUPYTER_YDOCEXTENSION_DISABLE_RTC", "FALSE").upper() == "TRUE"
)
