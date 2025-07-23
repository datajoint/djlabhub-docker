import logging
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: int = Field(
        default=logging.DEBUG, validation_alias="creds_updater_log_level"
    )
    debug: bool = Field(default=False, validation_alias="creds_updater_debug")
    auth_state_response_ttl_seconds: int = Field(
        default=60, validation_alias="creds_updater_ttl_seconds"
    )
    warn_on_expired_refresh: bool = Field(
        default=True, validation_alias="creds_updater_warn_on_expired_refresh"
    )
    expired_refresh_warn_message: str = Field(
        default=(
            "Unable to set DataJoint credentials automatically. Please reload "
            "Jupyter (e.g. by refreshing the page and restarting the kernel) "
            "and try again, or manually "
            "set the value of `datajoint.config['database.password']` "
            "in the notebook (see "
            "https://datajoint.com/docs/core/datajoint-python/0.14/client/credentials/ "
            "for details)."
        ),
        validation_alias="creds_updater_expired_refresh_warn_message",
    )


class JHubConfig(BaseSettings):
    api_url: str = Field(validation_alias="jupyterhub_api_url")
    token: str = Field(validation_alias="jupyterhub_api_token")
    user: str = Field(validation_alias="jupyterhub_user")


settings = Settings()
