import os
from typing import Any, List, Dict, Optional
from overrides import overrides
from traitlets import Bool, Unicode, default
import asyncio
import errno
import signal
import socket
import boto3
from gateway_provisioners import RemoteProvisionerBase
from gateway_provisioners.config_mixin import (
    max_poll_attempts,
    poll_interval,
    socket_timeout,
    ssh_port,
)

ec2_shutdown_wait_time = float(os.getenv("GP_EC2_SHUTDOWN_WAIT_TIME", "15.0"))


class EC2Provisioner(RemoteProvisionerBase):

    region_name = Unicode(
        default_value="us-east-2",
        config=True,
        help="""The region name to use when launching EC2 instances.""",
    )
    my_env_var = Bool(
        default_value=False,
        config=True,
        help="""Example of an env var that is passed as GP_MY_ENV_VAR to the kernel process.""",
    )

    # See https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html
    initial_states = {"pending", "running"}
    final_states = {"stopping", "stopped", "shutting-down", "terminated"}

    @property
    @overrides
    def has_process(self) -> bool:
        return self.local_proc is not None or self.application_id is not None

        # YARN impl
        return self.local_proc is not None or self.application_id is not None

    @overrides
    async def pre_launch(self, **kwargs: Any) -> dict[str, Any]:
        # DEBUG: use an existing EC2 instance if set in env
        self.application_id = os.environ.get("GP_EXISTING_EC2_INSTANCE_ID", None)
        if self.application_id is not None:
            self.log.info(f"Using existing EC2 instance: {self.application_id}")
        self.last_known_state = None

        # Logic to pass config params to the kernel process via env vars
        env_dict = kwargs.get("env")
        assert env_dict is not None
        env_dict["GP_MY_ENV_VAR"] = str(self.my_env_var)

        kwargs = await super().pre_launch(**kwargs)

        self._initialize_resource_manager(**kwargs)

        # checks to see if the queue resource is available
        # if not available, kernel startup is not attempted
        # self._confirm_yarn_queue_availability(**kwargs)

        self._last_not_found_message = None

        return kwargs

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        self.application_id = None
        self.last_known_state = None
        self.candidate_queue = None
        self.candidate_partition = None

        # Transfer impersonation enablement to env.  It is assumed that the kernelspec
        # logic will take the appropriate steps to impersonate the user identified by
        # KERNEL_USERNAME when impersonation_enabled is True.
        env_dict = kwargs.get("env")
        assert env_dict is not None
        env_dict["GP_IMPERSONATION_ENABLED"] = str(self.impersonation_enabled)

        kwargs = await super().pre_launch(**kwargs)

        self._initialize_resource_manager(**kwargs)

        # checks to see if the queue resource is available
        # if not available, kernel startup is not attempted
        self._confirm_yarn_queue_availability(**kwargs)

        return kwargs

    @overrides
    def get_shutdown_wait_time(self, recommended: float = 5.0) -> float:
        if recommended < ec2_shutdown_wait_time:
            recommended = ec2_shutdown_wait_time
            self.log.debug(
                f"{type(self).__name__} shutdown wait time adjusted to {recommended} seconds."
            )

        return recommended

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------


        # YARN applications tend to take longer than the default 5 second wait time.  Rather than
        # require a command-line option for those using YARN, we'll adjust based on a local env that
        # defaults to 15 seconds.  Note: we'll only adjust if the current wait time is shorter than
        # the desired value.
        if recommended < yarn_shutdown_wait_time:
            recommended = yarn_shutdown_wait_time
            self.log.debug(
                f"{type(self).__name__} shutdown wait time adjusted to {recommended} seconds."
            )

        return recommended

    @overrides
    async def poll(self) -> int | None:
        result = 0

        if self._get_application_id():
            assert self.application_id is not None
            state = self._query_app_state_by_id(self.application_id)
            self.log.debug(f"Checking if {state=} is in {EC2Provisioner.initial_states=}")
            if state in EC2Provisioner.initial_states:
                result = None

        # The following produces too much output (every 3 seconds by default), so commented-out at this time.
        self.log.debug("EC2Provisioner.poll, application ID: {}, kernel ID: {}, state: {}".
                      format(self.application_id, self.kernel_id, state))
        return result

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------


        # Submitting a new kernel/app to YARN will take a while to be ACCEPTED.
        # Thus application ID will probably not be available immediately for poll.
        # So will regard the application as RUNNING when application ID still in ACCEPTED or SUBMITTED state.

        result = 0

        if self._get_application_id():
            assert self.application_id is not None
            state = self._query_app_state_by_id(self.application_id)
            if state in EC2Provisioner.initial_states:
                result = None

        # The following produces too much output (every 3 seconds by default), so commented-out at this time.
        # self.log.debug("YarnProcessProxy.poll, application ID: {}, kernel ID: {}, state: {}".
        #               format(self.application_id, self.kernel_id, state))
        return result

    @overrides
    async def send_signal(self, signum: int) -> None:
        if signum == 0:
            await self.poll()
        elif signum == signal.SIGKILL:
            await self.kill()
        else:
            self.log.debug(f"Sending signal {signum} to {self.kernel_id}")
            await super().send_signal(signum)
        return

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------


        if signum == 0:
            await self.poll()
        elif signum == signal.SIGKILL:
            await self.kill()
        else:
            # Yarn api doesn't support the equivalent to interrupts, so take our chances
            # via a remote signal.  Note that this condition cannot check against the
            # signum value because alternate interrupt signals might be in play.
            await super().send_signal(signum)

    @overrides
    async def kill(self, restart: bool = False) -> None:
        state = None
        result = False
        if self._get_application_id():
            result, state = await self._shutdown_application()

        if result is False:  # We couldn't terminate via boto3, try remote signal
            # Must use super here, else infinite
            self.log.debug(f"Killing {self.kernel_id} via remote signal")
            result = await super().send_signal(signal.SIGKILL)  # type:ignore[func-returns-value]

        self.log.debug(
            f"EC2Provisioner.kill, application ID: {self.application_id}, "
            f"kernel ID: {self.kernel_id}, state: {state}, result: {result}"
        )
        return

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------


        state = None
        result = False
        if self._get_application_id():
            result, state = await self._shutdown_application()

        if result is False:  # We couldn't terminate via Yarn, try remote signal
            # Must use super here, else infinite
            result = await super().send_signal(signal.SIGKILL)  # type:ignore[func-returns-value]

        self.log.debug(
            f"YarnProvisioner.kill, application ID: {self.application_id}, "
            f"kernel ID: {self.kernel_id}, state: {state}, result: {result}"
        )

    @overrides
    async def terminate(self, restart: bool = False) -> None:
        """
        TODO: check restart from front-end
        """
        state = None
        if self._get_application_id():
            result, state = await self._shutdown_application()

        self.log.debug(
            f"EC2Provisioner.terminate, application ID: {self.application_id}, "
            f"kernel ID: {self.kernel_id}, state: {state}, result: {result}, restart: {restart}"
        )
        return

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        state = None
        if self._get_application_id():
            result, state = await self._shutdown_application()

        self.log.debug(
            f"YarnProvisioner.terminate, application ID: {self.application_id}, "
            f"kernel ID: {self.kernel_id}, state: {state}, result: {result}"
        )

    @overrides
    async def cleanup(self, restart: bool = False) -> None:
        # we might have a defunct process (if using waitAppCompletion = false) - so poll, kill, wait when we have
        # a local_proc.
        if self.local_proc:
            self.log.debug(
                f"EC2Provisioner.cleanup: Clearing possible defunct "
                f"process, pid={self.local_proc.pid}..."
            )

            if self.local_proc.poll():
                self.local_proc.kill()
            self.local_proc.wait()
            self.local_proc = None

        # reset application id to force new query - handles kernel restarts/interrupts
        self.application_id = None

        # for cleanup, we should call the superclass last
        await super().cleanup(restart=restart)
        return

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        # we might have a defunct process (if using waitAppCompletion = false) - so poll, kill, wait when we have
        # a local_proc.
        if self.local_proc:
            self.log.debug(
                f"YarnProvisioner.cleanup: Clearing possible defunct "
                f"process, pid={self.local_proc.pid}..."
            )

            if self.local_proc.poll():
                self.local_proc.kill()
            self.local_proc.wait()
            self.local_proc = None

        # reset application id to force new query - handles kernel restarts/interrupts
        self.application_id = None

        # for cleanup, we should call the superclass last
        await super().cleanup(restart=restart)

    @overrides
    async def get_provisioner_info(self) -> dict[str, Any]:
        provisioner_info = await super().get_provisioner_info()
        provisioner_info.update({"application_id": self.application_id})
        return provisioner_info

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        provisioner_info = await super().get_provisioner_info()
        provisioner_info.update({"application_id": self.application_id})
        return provisioner_info

    async def _remote_get_provisioner_info(self) -> Dict[str, Any]:
        """
        DOC
        """
        provisioner_info = await super().get_provisioner_info()
        provisioner_info.update(
            {
                "pid": self.pid,
                "pgid": self.pgid,
                "ip": self.ip,
                "assigned_ip": self.assigned_ip,
                "assigned_host": self.assigned_host,
                "comm_ip": self.comm_ip,
                "comm_port": self.comm_port,
                "tunneled_connect_info": self.tunneled_connect_info,
            }
        )
        return provisioner_info

    async def _base_get_provisioner_info(self) -> Dict[str, Any]:
        """
        DOC

        Captures the base information necessary for persistence relative to this instance.

        This enables applications that subclass `KernelManager` to persist a kernel provisioner's
        relevant information to accomplish functionality like disaster recovery or high availability
        by calling this method via the kernel manager's `provisioner` attribute.

        NOTE: The superclass method must always be called first to ensure proper serialization.
        """
        provisioner_info: Dict[str, Any] = {}
        provisioner_info["kernel_id"] = self.kernel_id
        provisioner_info["connection_info"] = self.connection_info
        return provisioner_info

    @overrides
    async def load_provisioner_info(self, provisioner_info: dict) -> None:
        await super().load_provisioner_info(provisioner_info)
        self.application_id = provisioner_info.get("application_id")
        return

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        await super().load_provisioner_info(provisioner_info)
        self.application_id = provisioner_info.get("application_id")

    async def _remote_load_provisioner_info(self, provisioner_info: dict) -> None:
        """
        DOC
        """
        await super().load_provisioner_info(provisioner_info)
        self.pid = provisioner_info.get("pid")
        self.pgid = provisioner_info.get("pgid")
        self.ip = provisioner_info.get("ip")
        self.assigned_ip = provisioner_info.get("assigned_ip")
        self.assigned_host = provisioner_info.get("assigned_host")
        self.comm_ip = provisioner_info.get("comm_ip")
        self.comm_port = provisioner_info.get("comm_port")
        self.tunneled_connect_info = provisioner_info.get("tunneled_connect_info")

    async def _base_load_provisioner_info(self, provisioner_info: Dict) -> None:
        """
        DOC

        Loads the base information necessary for persistence relative to this instance.

        The inverse of `get_provisioner_info()`, this enables applications that subclass
        `KernelManager` to re-establish communication with a provisioner that is managing
        a (presumably) remote kernel from an entirely different process that the original
        provisioner.

        NOTE: The superclass method must always be called first to ensure proper deserialization.
        """
        self.kernel_id = provisioner_info["kernel_id"]
        self.connection_info = provisioner_info["connection_info"]

    @overrides
    async def confirm_remote_startup(self) -> None:
        self.start_time = RemoteProvisionerBase.get_current_time()
        i = 0
        ready_to_connect = False  # we're ready to connect when we have a connection file to use
        while not ready_to_connect:
            i += 1
            await self.handle_launch_timeout()

            if self._get_application_id(ignore_final_states=True):
                # Once we have an application ID, start monitoring state, obtain assigned host and get connection info
                app_state = self._get_application_state()

                if app_state in EC2Provisioner.final_states:
                    error_message = (
                        f"KernelID: '{self.kernel_id}', ApplicationID: '{self.application_id}' "
                        f"unexpectedly found in state '{app_state}' during kernel startup!"
                    )
                    self.log_and_raise(RuntimeError(error_message))

                self.log.debug(
                    f"{i}: State: '{app_state}', Host: '{self.assigned_host}', "
                    f"KernelID: '{self.kernel_id}', ApplicationID: '{self.application_id}'"
                )

                if self.assigned_host != "":
                    ready_to_connect = await self.receive_connection_info()
            else:
                self.detect_launch_failure()
        return

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        self.start_time = RemoteProvisionerBase.get_current_time()
        i = 0
        ready_to_connect = False  # we're ready to connect when we have a connection file to use
        while not ready_to_connect:
            i += 1
            await self.handle_launch_timeout()

            if self._get_application_id(True):
                # Once we have an application ID, start monitoring state, obtain assigned host and get connection info
                app_state = self._get_application_state()

                if app_state in YarnProvisioner.final_states:
                    error_message = (
                        f"KernelID: '{self.kernel_id}', ApplicationID: '{self.application_id}' "
                        f"unexpectedly found in state '{app_state}' during kernel startup!"
                    )
                    self.log_and_raise(RuntimeError(error_message))

                self.log.debug(
                    f"{i}: State: '{app_state}', Host: '{self.assigned_host}', "
                    f"KernelID: '{self.kernel_id}', ApplicationID: '{self.application_id}'"
                )

                if self.assigned_host != "":
                    ready_to_connect = await self.receive_connection_info()
            else:
                self.detect_launch_failure()

    @overrides
    def log_kernel_launch(self, cmd: list[str]) -> None:
        assert self.local_proc is not None
        self.log.info(
            f"{self.__class__.__name__}: kernel launched. Hostname: {self.assigned_host or None}, "
            f"pid: {self.local_proc.pid}, Kernel ID: {self.kernel_id}, cmd: '{cmd}'"
        )
        return

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        assert self.local_proc is not None
        self.log.info(
            f"{self.__class__.__name__}: kernel launched. YARN RM: {self.rm_addr}, "
            f"pid: {self.local_proc.pid}, Kernel ID: {self.kernel_id}, cmd: '{cmd}'"
        )

    @overrides
    async def handle_launch_timeout(self) -> None:
        """
        YARN docstring:

        Checks to see if the kernel launch timeout has been exceeded while awaiting connection info.

        Note: This is a complete override of the superclass method.
        """
        await asyncio.sleep(poll_interval)
        time_interval = RemoteProvisionerBase.get_time_diff(
            self.start_time  # type:ignore[arg-type]
        )

        if time_interval > self.launch_timeout:
            reason = (
                f"Application ID is None. Failed to submit a new application to EC2 within "
                f"{self.launch_timeout} seconds.  Check server log for more information."
            )

            if self._get_application_id(ignore_final_states=True):
                assert self.application_id is not None
                self.log.debug(f"Checking if {self.application_id=} has state RUNNING")
                # TODO: align EC2 states with these states
                if self._query_app_state_by_id(self.application_id) != "running":
                    reason = (
                        f"EC2 resources unavailable after {time_interval} seconds for "
                        f"app {self.application_id}, launch timeout: {self.launch_timeout}!  "
                        "Check configuration."
                    )
                else:
                    reason = (
                        f"App {self.application_id} is RUNNING, but waited too long "
                        f"({self.launch_timeout} secs) to get connection file.  "
                        f"Check logs for more information."
                    )
            await self.kill()
            timeout_message = f"KernelID: '{self.kernel_id}' launch timeout due to: {reason}"
            self.log_and_raise(TimeoutError(timeout_message))
        return

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        await asyncio.sleep(poll_interval)
        time_interval = RemoteProvisionerBase.get_time_diff(
            self.start_time  # type:ignore[arg-type]
        )

        if time_interval > self.launch_timeout:
            reason = (
                f"Application ID is None. Failed to submit a new application to YARN within "
                f"{self.launch_timeout} seconds.  Check server log for more information."
            )

            if self._get_application_id(True):
                assert self.application_id is not None
                if self._query_app_state_by_id(self.application_id) != "RUNNING":
                    reason = (
                        f"YARN resources unavailable after {time_interval} seconds for "
                        f"app {self.application_id}, launch timeout: {self.launch_timeout}!  "
                        "Check YARN configuration."
                    )
                else:
                    reason = (
                        f"App {self.application_id} is RUNNING, but waited too long "
                        f"({self.launch_timeout} secs) to get connection file.  "
                        f"Check YARN logs for more information."
                    )
            await self.kill()
            timeout_message = f"KernelID: '{self.kernel_id}' launch timeout due to: {reason}"
            self.log_and_raise(TimeoutError(timeout_message))

    async def _shutdown_application(self) -> tuple[bool | None, str]:
        """
        Shut down app (EC2 instance)

        YARN docstring:
        Shuts down the YARN application, returning None if final state is confirmed, False otherwise.
        """
        result = False
        assert self.application_id is not None
        self._kill_app_by_id(self.application_id)
        # Check that state has moved to a final state (most likely KILLED)
        i = 1
        state = self._query_app_state_by_id(self.application_id)
        assert state is not None
        while state not in EC2Provisioner.final_states and i <= max_poll_attempts:
            await asyncio.sleep(poll_interval)
            state = self._query_app_state_by_id(self.application_id)
            i += 1

        if state in EC2Provisioner.final_states:
            result = None

        assert state is not None
        return result, state

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        result = False
        assert self.application_id is not None
        self._kill_app_by_id(self.application_id)
        # Check that state has moved to a final state (most likely KILLED)
        i = 1
        state = self._query_app_state_by_id(self.application_id)
        assert state is not None
        while state not in YarnProvisioner.final_states and i <= max_poll_attempts:
            await asyncio.sleep(poll_interval)
            state = self._query_app_state_by_id(self.application_id)
            i += 1

        if state in YarnProvisioner.final_states:
            result = None

        assert state is not None
        return result, state

    # ----------------------------------------------------------------------
    # Client Low-Level Interface
    # ----------------------------------------------------------------------

    def _initialize_resource_manager(self, **kwargs: dict[str, Any] | None) -> None:
        """
        Initialize the boto3 EC2 client used for this kernel's lifecycle.
        Sets a `client` attribute on the instance.

        YARN docstring:

        Initialize the Hadoop YARN Resource Manager instance used for this kernel's lifecycle.
        """
        self.client = boto3.client("ec2", region_name=self.region_name)
        return

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        endpoints = None
        if self.yarn_endpoint:
            endpoints = [self.yarn_endpoint]

            # Only check alternate if "primary" is set.
            if self.alt_yarn_endpoint:
                endpoints.append(self.alt_yarn_endpoint)

        if self.yarn_endpoint_security_enabled:
            from requests_kerberos import HTTPKerberosAuth  # type:ignore[import-not-found]

            auth = HTTPKerberosAuth()
        else:
            # If we have the appropriate version of yarn-api-client, use its SimpleAuth class.
            # This allows EG to continue to issue requests against the YARN api when anonymous
            # access is not allowed. (Default is to allow anonymous access.)
            try:
                from yarn_api_client.auth import SimpleAuth  # type:ignore[import-untyped]

                auth = SimpleAuth(self.kernel_username)
                self.log.debug(
                    f"Using SimpleAuth with '{self.kernel_username}' against endpoints: {endpoints}"
                )
            except ImportError:
                auth = None

        self.resource_mgr = ResourceManager(
            service_endpoints=endpoints, auth=auth, verify=cert_path
        )

        self.rm_addr = self.resource_mgr.get_active_endpoint()

    def _get_application_state(self) -> str | None:
        """
        This method assumes that we already have called _get_application_id first,
        which sets last_known_state and application_id.

        This method updates attributes:

        - assigned_host
        - assigned_ip
        - last_known_state

        given the response from _query_app_by_id.

        YARN docstring:
        Gets the current application state using the application_id already obtained.

        Once the assigned host has been identified, 'amHostHttpAddress' is no longer accessed.
        """
        app_state = self.last_known_state
        assert self.application_id is not None
        app = self._query_app_by_id(self.application_id)
        if app:
            if app.get("state"):
                app_state = app.get("state")
                self.last_known_state = app_state

            if self.assigned_host == "" and app.get("amHostHttpAddress"):
                # example amHostHttpAddress: "host.domain.com:8042"
                self.assigned_host = app.get("amHostHttpAddress").split(  # type:ignore[union-attr]
                    ":"
                )[0]
                # Set the assigned ip to the actual host where the application landed.
                self.assigned_ip = socket.gethostbyname(self.assigned_host)

        return app_state

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        app_state = self.last_known_state
        assert self.application_id is not None
        app = self._query_app_by_id(self.application_id)
        if app:
            if app.get("state"):
                app_state = app.get("state")
                self.last_known_state = app_state

            if self.assigned_host == "" and app.get("amHostHttpAddress"):
                # example amHostHttpAddress: "host.domain.com:8042"
                self.assigned_host = app.get("amHostHttpAddress").split(  # type:ignore[union-attr]
                    ":"
                )[0]
                # Set the assigned ip to the actual host where the application landed.
                self.assigned_ip = socket.gethostbyname(self.assigned_host)

        return app_state

    def _get_application_id(self, ignore_final_states=False) -> str | None:
        """
        TODO

        TODO: sometimes called with ignore_final_states=True

        Return the kernel's application ID (EC2 instance ID) if available, otherwise None.

        :returns Optional[str] - the application ID or None if not available

        YARN docstring:

        Return the kernel's YARN application ID if available, otherwise None.

        If we're obtaining application_id from scratch, do not consider kernels in final states.
        :param ignore_final_states:
        :returns Optional[str] - the YARN application ID or None if not available
        """

        """
        Plan

        1. Call _query_app_by_name to retrieve application by using kernel_id as the unique app name.
            - Look for EC2 instances with the kernel_id in their tags.
        2. Take the app: dict response and parse the ['id'] and set as application_id to indicate success
        3. Always return None, and set application_id to None (or leave) if not found, which will trigger retry
        4. Also update last_known_state?
        """

        if not self.application_id:
            app = self._query_app_by_name(self.kernel_id)
            state_condition = True
            if isinstance(app, dict):
                state = app.get("state")
                self.last_known_state = state

                if ignore_final_states:
                    state_condition = state not in EC2Provisioner.final_states

                if len(app.get("id", "")) > 0 and state_condition:
                    self.application_id = app["id"]
                    time_interval = RemoteProvisionerBase.get_time_diff(
                        self.start_time  # type:ignore[arg-type]
                    )
                    self.log.info(
                        f"ApplicationID: '{app['id']}' assigned for KernelID: '{self.kernel_id}', "
                        f"state: {state}, {time_interval} seconds after starting."
                    )
            if not self.application_id:
                self.log.debug(
                    f"ApplicationID not yet assigned for KernelID: '{self.kernel_id}' - retrying..."
                )
        return self.application_id

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        if not self.application_id:
            app = self._query_app_by_name(self.kernel_id)
            state_condition = True
            if isinstance(app, dict):
                state = app.get("state")
                self.last_known_state = state

                if ignore_final_states:
                    state_condition = state not in YarnProvisioner.final_states

                if len(app.get("id", "")) > 0 and state_condition:
                    self.application_id = app["id"]
                    time_interval = RemoteProvisionerBase.get_time_diff(
                        self.start_time  # type:ignore[arg-type]
                    )
                    self.log.info(
                        f"ApplicationID: '{app['id']}' assigned for KernelID: '{self.kernel_id}', "
                        f"state: {state}, {time_interval} seconds after starting."
                    )
            if not self.application_id:
                self.log.debug(
                    f"ApplicationID not yet assigned for KernelID: '{self.kernel_id}' - retrying..."
                )
        return self.application_id

    def _get_first_instance(self, resp: dict, kernel_id: Optional[str] = None) -> dict | None:
        """
        Get first instance from the first reservation from a boto3 response.
        Returns None if no instances are found, and a single instance dictionary
        if one is found.
        """
        resis = resp.get("Reservations", [])
        if len(resis) > 1:
            self.log.warning(f"Multiple instances found with kernel ID '{kernel_id}' - using the first one.")
        resi = resis[0] if resis else None
        if resi is None:
            self.log.warning(RuntimeError(f"Kernel ID '{kernel_id}' not found in EC2 instances. Continuing..."))
            return
        instances = resi.get("Instances", [])
        if len(instances) > 1:
            self.log.warning(f"Multiple instances found with kernel ID '{kernel_id}' - using the first one.")
        instance = instances[0] if instances else None
        if instance is None:
            self.log.warning(RuntimeError(f"Kernel ID '{kernel_id}' not found in EC2 instances. Continuing..."))
            return
        return instance


    def _query_app_by_name(self, kernel_id: str) -> Dict[str, str] | None:
        """
        Retrieve application by using kernel_id as the unique app name.

        The application (EC2 instance) is identified by the kernel_id in its tags,
        and DEBUG, is assumed to exist already.

        :param kernel_id: as the unique app name for query
        :return: The JSON object of an application with keys name, ami, and id,
        or None on failure

        YARN docstring:

        Retrieve application by using kernel_id as the unique app name.

        With the started_time_begin as a parameter to filter applications started earlier than the target one from YARN.
        When submit a new app, it may take a while for YARN to accept and run and generate the application ID.
        Note: if a kernel restarts with the same kernel id as app name, multiple applications will be returned.
        For now, the app/kernel with the top most application ID will be returned as the target app, assuming the app
        ID will be incremented automatically on the YARN side.

        :param kernel_id: as the unique app name for query
        :return: The JSON object of an application or None on failure
        """
        try:
            resp = self.client.describe_instances(Filters=[
                {"Name": "tag:wbn_kernel_id", "Values": [kernel_id]}
            ])
        except OSError as sock_err:
            if sock_err.errno == errno.ECONNREFUSED:
                self.log.warning(
                    f"YARN RM address: '{self.rm_addr}' refused the connection.  "
                    f"Is the resource manager running?"
                )
            else:
                self.log.warning(
                    f"Query for kernel ID '{kernel_id}' failed with exception: "
                    f"{type(sock_err)} - '{sock_err}'.  Continuing..."
                )
            return
        except Exception as e:
            self.log.warning(
                f"Query for kernel ID '{kernel_id}' failed with exception: "
                f"{type(e)} - '{e}'.  Continuing..."
            )
            return

        instance = self._get_first_instance(resp, kernel_id)
        if instance is None and self._last_not_found_message is None:
            self.log.warning(f"Kernel ID '{kernel_id}' not found in EC2 instances. Continuing...")
            self._last_not_found_message = True
            return
        # TODO: catch KeyError
        return dict(
            id=instance["InstanceId"],
            ami=instance.get["ImageId"],
            state=instance["State"]["Name"],
        )

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        top_most_app_id = ""
        target_app = None
        try:
            response = self.resource_mgr.cluster_applications(
                started_time_begin=str(self.start_time)
            )
        except OSError as sock_err:
            if sock_err.errno == errno.ECONNREFUSED:
                selfPublicDnsName.log.warning(
                    f"YARN RM address: '{self.rm_addr}' refused the connection.  "
                    f"Is the resource manager running?"
                )
            else:
                self.log.warning(
                    f"Query for kernel ID '{kernel_id}' failed with exception: "
                    f"{type(sock_err)} - '{sock_err}'.  Continuing..."
                )
        except Exception as e:
            self.log.warning(
                f"Query for kernel ID '{kernel_id}' failed with exception: "
                f"{type(e)} - '{e}'.  Continuing..."
            )
        else:
            data = response.data
            if (
                isinstance(type, dict)
                and isinstance(data.get("apps"), dict)
                and "app" in data.get("apps")
            ):
                for app in data["apps"]["app"]:
                    if app.get("name", "").find(kernel_id) >= 0 and app.get("id") > top_most_app_id:
                        target_app = app
                        top_most_app_id = app.get("id")
        return target_app

    def _query_app_by_id(self, app_id: str) -> dict | None:
        """
        This method gets the current app (EC2 instance) using boto3 client, given
        the application ID (EC2 instance ID)

        YARN docstring:
        Retrieve an application by application ID.

        :param app_id
        :return: The JSON object of an application or None on failure.
        """
        try:
            resp = self.client.describe_instances(InstanceIds=[app_id])
        except Exception as e:
            self.log.warning(
                f"Query for application ID '{app_id}' failed with exception: '{e}'.  Continuing..."
            )
            return

        instance = self._get_first_instance(resp, self.kernel_id)
        if instance is None:
            self.log.warning(f"Kernel ID '{self.kernel_id}' not found in EC2 instances. Continuing...")
            return

        return dict(
            id=instance["InstanceId"],
            ami=instance["ImageId"],
            # example amHostHttpAddress: "host.domain.com:8042"
            amHostHttpAddress=instance["PublicDnsName"],
            public_ip_address=instance.get("PublicIpAddress"),
            state=instance["State"]["Name"],
        )

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        app = None
        try:
            response = self.resource_mgr.cluster_application(application_id=app_id)
        except Exception as e:
            self.log.warning(
                f"Query for application ID '{app_id}' failed with exception: '{e}'.  Continuing..."
            )
        else:
            data = response.data
            if isinstance(data, dict) and "app" in data:
                app = data["app"]

        return app

    def _query_app_state_by_id(self, app_id: str) -> str | None:
        """
        Using client, query for the state of an application and update
        last_known_state with the result.

        YARN docstring:

        Return the state of an application. If a failure occurs, the last known state is returned.

        :param app_id:
        :return: application state (str)
        """
        self.log.debug(f"Querying for application state of '{app_id}'...")
        try:
            resp = self.client.describe_instances(InstanceIds=[app_id])
        except Exception as e:
            self.log.warning(
                f"Query for application '{app_id}' state failed with exception: '{e}'.  "
                f"Continuing with last known state = '{state}'..."
            )
            return

        instance = self._get_first_instance(resp, self.kernel_id)
        if instance is None:
            self.log.warning(f"Kernel ID '{self.kernel_id}' not found in EC2 instances. Continuing...")
            return
        state = instance["State"]["Name"]
        self.last_known_state = state
        return state

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        state = self.last_known_state
        try:
            response = self.resource_mgr.cluster_application_state(application_id=app_id)
        except Exception as e:
            self.log.warning(
                f"Query for application '{app_id}' state failed with exception: '{e}'.  "
                f"Continuing with last known state = '{state}'..."
            )
        else:
            state = response.data["state"]
            self.last_known_state = state

        return state

    def _kill_app_by_id(self, app_id: str) -> dict:
        """
        Kill application using boto3.

        YARN docstring:
        Kill an application. If the app's state is FINISHED or FAILED, it won't be changed to KILLED.

        :param app_id
        :return: The JSON response of killing the application.
        """
        try:
            response = self.client.terminate_instances(InstanceIds=[app_id])
        except Exception as e:
            self.log.warning(
                f"Termination of application '{app_id}' failed with exception: '{e}'.  Continuing..."
            )
            return
        return response

        # ----------------------------------------------------------------------
        # YARN impl
        # ----------------------------------------------------------------------

        response = {}
        try:
            response = self.resource_mgr.cluster_application_kill(application_id=app_id)
        except Exception as e:
            self.log.warning(
                f"Termination of application '{app_id}' failed with exception: '{e}'.  Continuing..."
            )
        return response
