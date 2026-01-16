import os
import time
import logging
import requests
import jwt
from functools import lru_cache
from typing import Dict, Tuple, Optional
from packaging import version
from datajoint.settings import config as dj_config
from pydantic import ValidationError
from .settings import settings, JHubConfig

Token = Optional[str]

@lru_cache(maxsize=1)
def get_token_from_jhub_auth_state(
    api_url: str, token: str, user: str, logger=None, ttl_hash=None
) -> Tuple[Token, Token]:
    """
    Get the access and refresh tokens from the `auth_state` object returned
    from the JupyterHub API. This function is cached for a configurable number
    of seconds, defined by `ttl_hash`. If `ttl_hash` is not provided, the
    function cache will never expire.
    """
    del ttl_hash
    logger = logger or logging.getLogger(__name__)
    url = api_url + f"/users/{user}"
    try:
        resp = requests.get(
            url,
            headers={
                "Authorization": f"token {token}",
            },
            timeout=(0.5, 0.5),
            verify=False,
        )
    except (requests.RequestException,) as e:
        logger.error(f"Request to {url=} failed with {e}")
        return "", ""
    logger.debug(f"Request to {url=} responded with {resp=}")
    if resp.status_code >= 300:
        logger.error(
            f"Request to {url=} failed returning status code {resp.status_code}"
        )
        return "", ""
    auth_state = resp.json().get("auth_state", dict())
    return auth_state.get("access_token"), auth_state.get("refresh_token")

def decode_token(tok: str) -> Dict:
    """
    Decode a JWT token using PyJWT.
    """
    if version.parse(jwt.__version__) < version.parse("2.0.0"):
        kwargs = dict(verify=False)
    else:
        kwargs = dict(options=dict(verify_signature=False))
    return jwt.decode(tok, algorithms=["RS256"], **kwargs)

def check_token_expiry(tok: str, logger=None, token_type: str = "access") -> int:
    """
    Returns number of seconds until token expiry.
    """
    logger = logger or logging.getLogger(__name__)
    tok: dict = decode_token(tok)
    if "exp" not in tok:
        logger.error(f"{token_type.title()} token has no expiry time.")
        return 0
    now = int(time.time())
    sec_remaining = tok["exp"] - now
    logger.info(
        f"{token_type.title()} token has {sec_remaining:0.2f} seconds until expiry"
    )
    return sec_remaining

def get_ttl_hash(ttl_seconds=60) -> int:
    """
    Return the same value within `ttl_seconds` time period.
    Adapted from https://stackoverflow.com/a/55900800
    """
    return round(time.time() / float(ttl_seconds))

def setup_database_password(logger=None):
    logger = logger or logging.getLogger(__name__)
    try:
        cfg = JHubConfig()
    except ValidationError as e:
        logger.warn(f"Invalid JHubConfig: {e}")
        return
    access_token, refresh_token = get_token_from_jhub_auth_state(
        cfg.api_url,
        cfg.token,
        cfg.user,
        logger=logger,
        ttl_hash=get_ttl_hash(ttl_seconds=settings.auth_state_response_ttl_seconds),
    )
    if settings.debug:
        logger.debug(f"{get_token_from_jhub_auth_state.cache_info()=}")
        expiry: int = check_token_expiry(
            access_token, logger=logger, token_type="access"
        )
        logger.debug(
            f"Access token ending with {access_token[-7:]} expires in {expiry} seconds"
        )
    refresh_expiry: int = check_token_expiry(
        refresh_token, logger=logger, token_type="refresh"
    )
    if refresh_expiry > 0:
        dj_config["database.password"] = access_token
        os.environ['DJ_PASSWORD'] = access_token
        if settings.debug:
            logger.debug(
                f"Refresh token ending with {refresh_token - 7:]} "
                f"expires in {refresh_expiry} seconds"
            )
    elif settings.warn_on_expired_refresh:
        logger.warn(settings.expired_refresh_warn_message)
