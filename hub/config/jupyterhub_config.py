import os
import pwd
import json
import jwt
import time
from packaging import version
from oauthenticator.generic import GenericOAuthenticator
from traitlets import Tuple, Dict
from traitlets.config import Config
from urllib import request, parse
from urllib.error import HTTPError

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
# c.JupyterHub.authenticator_class = "jupyterhub.auth.DummyAuthenticator"


class RefreshingAuthenticator(GenericOAuthenticator):
    """Custom Authenticator that refreshes OAuth tokens when needed."""

    def _refresh_token(self, refresh_token: str) -> Tuple:
        values = dict(
            grant_type = 'refresh_token',
            client_id = self.client_id,
            client_secret = self.client_secret,
            refresh_token = refresh_token
        )
        data = parse.urlencode(values).encode('ascii')

        req = request.Request(self.token_url, data)
        with request.urlopen(req) as response:
            data = json.loads(response.read())
            return (data.get('access_token', None), data.get('refresh_token', None))

    def _decode_token(self, token: str) -> Dict:
        if version.parse(jwt.__version__).major >= 2:
            kw = dict(options=dict(verify_signature=False))
        else:
            kw = dict(verify=False)
        return jwt.decode(token, algorithms='RS256', **kw)

    async def refresh_user(self, user, handler=None):
        """
        Refresh user's OAuth tokens. This is called when user info is requested
        and has passed more than "auth_refresh_age" seconds.
        """
        self.log.info('Refreshing OAuth tokens for user %s' % user.name)
        try:
            auth_state = await user.get_auth_state()
            decoded_access_token = self._decode_token(auth_state['access_token'])
            decoded_refresh_token = self._decode_token(auth_state['refresh_token'])
            diff_access = decoded_access_token['exp'] - time.time()
            # If we request the offline_access scope, our refresh token won't have expiration
            diff_refresh = (decoded_refresh_token['exp'] - time.time()) if 'exp' in decoded_refresh_token else 0
            if diff_access > self.auth_refresh_age:
                # Access token is still valid and will stay until next refresh
                return True
            elif diff_refresh < 0:
                # Refresh token not valid, need to re-authenticate again
                return False
            else:
                # We need to refresh access token (which will also refresh the refresh token)
                access_token, refresh_token = self._refresh_token(auth_state['refresh_token'])
                auth_state['access_token'] = access_token
                auth_state['refresh_token'] = refresh_token
                self.log.debug('User %s OAuth tokens refreshed' % user.name)
                return {'auth_state': auth_state}
        except HTTPError as e:
            self.log.error("Failure calling the renew endpoint: %s (code: %s)" % (e.read(), e.code))
        except Exception:
            self.log.error("Failed to refresh the OAuth tokens", exc_info=True)
        return False


## TODO - callback_url needs to enable ssl
c.JupyterHub.ssl_key = '/etc/letsencrypt/live/fakeservices.datajoint.io/privkey.pem'
c.JupyterHub.ssl_cert = '/etc/letsencrypt/live/fakeservices.datajoint.io/fullchain.pem'
c.JupyterHub.authenticator_class = RefreshingAuthenticator
c.GenericOAuthenticator.client_id = os.getenv("OAUTH2_CLIENT_ID")
c.GenericOAuthenticator.client_secret = os.getenv("OAUTH2_CLIENT_SECRET")
c.GenericOAuthenticator.oauth_callback_url = "https://127.0.0.1:8000/hub/oauth_callback"
c.GenericOAuthenticator.authorize_url = "https://keycloak-qa.datajoint.io/realms/datajoint/protocol/openid-connect/auth"
c.GenericOAuthenticator.token_url = "https://keycloak-qa.datajoint.io/realms/datajoint/protocol/openid-connect/token"
c.GenericOAuthenticator.userdata_url = "https://keycloak-qa.datajoint.io/realms/datajoint/protocol/openid-connect/userinfo"
c.GenericOAuthenticator.login_service = "Datajoint"
c.GenericOAuthenticator.username_claim = "preferred_username"
c.GenericOAuthenticator.enable_auth_state = True
c.GenericOAuthenticator.scope = ["openid"]
c.GenericOAuthenticator.claim_groups_key = "groups"
c.GenericOAuthenticator.admin_groups = ["datajoint"]

# If your authenticator needs extra configurations, set them in the pre-spawn hook
def pre_spawn_hook(authenticator, spawner, auth_state):
    print(f"{auth_state=}")
    # spawner.environment['ACCESS_TOKEN'] = auth_state['exchanged_tokens']['eos-service']
    # spawner.environment['OAUTH_INSPECTION_ENDPOINT'] = authenticator.userdata_url.replace('https://', '')
    # spawner.user_roles = authenticator.get_roles_for_token(auth_state['access_token'])
    # spawner.user_uid = auth_state['oauth_user']['cern_uid']
c.KeyCloakAuthenticator.pre_spawn_hook = pre_spawn_hook

# Internal auth expiry
# c.JupyterHub.cookie_max_age_days = 0.00028 # 1 minute

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
    # "DJLABHUB_REPO": "https://github.com/datajoint/datajoint-tutorials.git",
    # "DJLABHUB_REPO_BRANCH": "main",
    # "DJLABHUB_REPO_INSTALL": "TRUE",
    ## Jupyter Config
    # "JUPYTER_SERVER_APP_IP": "0.0.0.0",
    # "JUPYTER_SERVER_APP_PASSWORD": "",
    # "JUPYTER_SERVER_APP_PORT": "8889",
    # "JUPYTER_SERVER_APP_ROOT_DIR": "/home/jovyan",
    "JUPYTER_FILE_CONTENTS_MANAGER_ROOT_DIR": "/home/jovyan",
    "JUPYTER_YDOCEXTENSION_DISABLE_RTC": "TRUE",
}

# def auth_state_hook(spawner, auth_state):
#     # print(f"{auth_state=}")
#     spawner.environment['DJ_USER'] = auth_state['oauth_user']['preferred_username']
#     spawner.environment['DJ_PASS'] = auth_state['access_token']
#     spawner.environment['DJ_HOST'] = 'percona-qa.datajoint.io'

# # Set profile options
# c.Spawner.auth_state_hook = auth_state_hook

c.JupyterHub.load_roles = [
    {
        "name": "user",
        "description": "User Role for accessing auth_state via API",
        "scopes": ["self", "admin:auth_state!user"],
        "services": [],
    }, {
        "name": "server",
        "description": "Allows parties to start and stop user servers",
        "scopes": ["access:servers!user", "read:users:activity!user", "users:activity!user", "admin:auth_state!user"],
        "services":[]
    }
]