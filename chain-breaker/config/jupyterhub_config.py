import os
import pwd
from traitlets.config import Config

c = Config() if "c" not in locals() else c

# get the current user
user = [u for u in pwd.getpwall() if u.pw_uid == os.getuid()][0]

## Allow named single-user servers per user
#  Default: False
# c.JupyterHub.allow_named_servers = False
c.JupyterHub.allow_named_servers = True
