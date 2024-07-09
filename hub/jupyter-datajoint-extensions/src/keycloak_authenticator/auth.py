# Original Author: Prasanth Kothuri, Diogo Castro 2020
# Original Copyright CERN

# Adapted from https://raw.githubusercontent.com/swan-cern/jupyterhub-extensions/KeyCloakAuthenticator/v1.0.0/KeyCloakAuthenticator/keycloakauthenticator/auth.py
# by Ethan Ho 2024

"""KeyCloakAuthenticator"""

from packaging import version
from jupyterhub.handlers import LogoutHandler
from jupyterhub.utils import maybe_future
from oauthenticator.generic import GenericOAuthenticator
from tornado import gen, web
from traitlets import Unicode, Set, Bool, Any, List
import jwt, os, pwd, time, json
from urllib import request, parse
from urllib.error import HTTPError


class KeyCloakAuthenticator(GenericOAuthenticator):
    """KeyCloakAuthenticator based on upstream jupyterhub/oauthenticator"""

    def _refresh_token(self, refresh_token):
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

    def _decode_token(self, token):
        if self._jwt_version.major >= 2:
            kw = dict(options=dict(verify_signature=False))
        else:
            kw = dict(verify=False)
        return jwt.decode(token, algorithms='RS256', **kw)

    @property
    def _jwt_version(self):
        return version.parse(jwt.__version__)

    async def refresh_user(self, user, handler=None):
        """
            Refresh user's OAuth tokens.
            This is called when user info is requested and
            has passed more than "auth_refresh_age" seconds.
        """
        self.log.info('Refreshing OAuth tokens for user %s' % user.name)

        try:
            # Retrieve user authentication info, decode, and check if refresh is needed
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
                # auth_state['exchanged_tokens'] = self._exchange_tokens(access_token)

                self.log.info('User %s OAuth tokens refreshed' % user.name)
                return {
                    'auth_state': auth_state
                }

        except HTTPError as e:
            self.log.error("Failure calling the renew endpoint: %s (code: %s)" % (e.read(), e.code))

        except Exception:
            self.log.error("Failed to refresh the OAuth tokens", exc_info=True)

        return False
