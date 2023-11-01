import os
import pwd

# Configuration file for lab.

# c = get_config()  # noqa
from traitlets.config import Config

c = Config() if "c" not in locals() else c

# get the current user
user = [u for u in pwd.getpwall() if u.pw_uid == os.getuid()][0]

## The default URL to redirect to from `/`
#  Default: '/lab'
jupyter_lab_default_url = os.getenv("JUPYTER_LAB_APP_DEFAULT_URL")
c.LabApp.default_url = (
    "/lab/tree{}".format(
        jupyter_lab_default_url.replace(
            os.getenv("JUPYTER_FILE_CONTENTS_MANAGER_ROOT_DIR", "/home/jovyan"), ""
        )
    )
    if jupyter_lab_default_url
    else "/lab"
)
