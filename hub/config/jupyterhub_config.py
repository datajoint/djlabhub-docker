import os
import pwd
from traitlets.config import Config

c = Config() if "c" not in locals() else c

# get the current user
user = [u for u in pwd.getpwall() if u.pw_uid == os.getuid()][0]

## Class for authenticating users.
#
#          This should be a subclass of :class:`jupyterhub.auth.Authenticator`
#
#          with an :meth:`authenticate` method that:
#
#          - is a coroutine (asyncio or tornado)
#          - returns username on success, None on failure
#          - takes two arguments: (handler, data),
#            where `handler` is the calling web.RequestHandler,
#            and `data` is the POST form data from the login page.
#
#          .. versionchanged:: 1.0
#              authenticators may be registered via entry points,
#              e.g. `c.JupyterHub.authenticator_class = 'pam'`
#
#  Currently installed:
#    - default: jupyterhub.auth.PAMAuthenticator
#    - dummy: jupyterhub.auth.DummyAuthenticator
#    - null: jupyterhub.auth.NullAuthenticator
#    - pam: jupyterhub.auth.PAMAuthenticator
#  Default: 'jupyterhub.auth.PAMAuthenticator'
c.JupyterHub.authenticator_class = "jupyterhub.auth.DummyAuthenticator"

# ## TODO - callback_url needs to enable ssl
# c.JupyterHub.authenticator_class = "oauthenticator.generic.GenericOAuthenticator"
# c.GenericOAuthenticator.client_id = os.getenv("OAUTH2_CLIENT_ID")
# c.GenericOAuthenticator.client_secret = os.getenv("OAUTH2_CLIENT_SECRET")
# c.GenericOAuthenticator.oauth_callback_url = "https://127.0.0.1:8000/hub/oauth_callback"
# c.GenericOAuthenticator.authorize_url = "https://keycloak-qa.datajoint.io/realms/datajoint/protocol/openid-connect/auth"
# c.GenericOAuthenticator.token_url = "https://keycloak-qa.datajoint.io/realms/datajoint/protocol/openid-connect/token"
# c.GenericOAuthenticator.userdata_url = "https://keycloak-qa.datajoint.io/realms/datajoint/protocol/openid-connect/userinfo"
# c.GenericOAuthenticator.login_service = "Datajoint"
# c.GenericOAuthenticator.username_claim = "preferred_username"
# c.GenericOAuthenticator.enable_auth_state = True
# c.GenericOAuthenticator.scope = ["openid"]
# c.GenericOAuthenticator.claim_groups_key = "groups"
# c.GenericOAuthenticator.admin_groups = ["datajoint"]

## The class to use for spawning single-user servers.
#
#          Should be a subclass of :class:`jupyterhub.spawner.Spawner`.
#
#          .. versionchanged:: 1.0
#              spawners may be registered via entry points,
#              e.g. `c.JupyterHub.spawner_class = 'localprocess'`
#
#  Currently installed:
#    - default: jupyterhub.spawner.LocalProcessSpawner
#    - localprocess: jupyterhub.spawner.LocalProcessSpawner
#    - simple: jupyterhub.spawner.SimpleLocalProcessSpawner
#  Default: 'jupyterhub.spawner.LocalProcessSpawner'
c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"

## The ip address for the Hub process to *bind* to.
#
#          By default, the hub listens on localhost only. This address must be accessible from
#          the proxy and user servers. You may need to set this to a public ip or '' for all
#          interfaces if the proxy or user servers are in containers or on a different host.
#
#          See `hub_connect_ip` for cases where the bind and connect address should differ,
#          or `hub_bind_url` for setting the full bind URL.
#  Default: '127.0.0.1'
c.JupyterHub.hub_ip = ""

c.DockerSpawner.network_name = os.getenv("DOCKER_NETWORK_NAME", "jupyterhub_network")
c.DockerSpawner.start_timeout = 60
# https://github.com/jupyterhub/jupyterhub/issues/2913#issuecomment-580535422
c.Spawner.http_timeout = 60
c.Spawner.start_timeout = 60
c.DockerSpawner.container_image = "datajoint/djlabhub:singleuser-4.0.2-py3.10"

c.DockerSpawner.environment = {
    ## Jupyter Official Environment Variables
    "DOCKER_STACKS_JUPYTER_CMD": "lab",
    ## Extended by Datajoint
    ## Before Start Hook
    "DJLABHUB_REPO": "https://github.com/datajoint/datajoint-tutorials.git",
    "DJLABHUB_REPO_BRANCH": "main",
    "DJLABHUB_REPO_INSTALL": "TRUE",
    ## Jupyter Config
    # "JUPYTER_SERVER_APP_IP": "0.0.0.0",
    # "JUPYTER_SERVER_APP_PASSWORD": "",
    # "JUPYTER_SERVER_APP_PORT": "8889",
    # "JUPYTER_SERVER_APP_ROOT_DIR": "/home/jovyan",
    "JUPYTER_FILE_CONTENTS_MANAGER_ROOT_DIR": "/home/jovyan",
    "JUPYTER_YDOCEXTENSION_DISABLE_RTC": "TRUE",
}
