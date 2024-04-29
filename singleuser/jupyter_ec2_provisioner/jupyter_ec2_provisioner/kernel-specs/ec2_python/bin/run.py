#!/opt/conda/bin/python3

"""
Ethan Ho 4/26/2024

Script that launches an IPython Jupyter kernel on an EC2 instance.

Usage:
    run.py --kernel-id=191af622-a3f5-4982-9af3-e4d98d9cf0b6 \
           --port-range=0..0 \
           --response-address=172.27.0.2:8877 \
           --public-key=12345 \
           --kernel-class-name=ipykernel.ipkernel.IPythonKernel \
           --help
"""

import sys
import typer
from pathlib import Path
from typing_extensions import Annotated
from jupyter_ec2_provisioner.boto3_utils import (
    start_nb_worker,
)


def main(
    kernel_id: Annotated[str, typer.Option(help="Kernel ID. Example: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")] = "",
    port_range: Annotated[str, typer.Option(help="Port range. Example: 0..0")] = "",
    response_address: Annotated[str, typer.Option(help="Response address. Example: 172.27.0.2:8877")] = "",
    public_key: Annotated[str, typer.Option(help="Public key. Example: 12345678")] = "",
    kernel_class_name: Annotated[str, typer.Option(help="Kernel class name. Example: ipykernel.ipkernel.IPythonKernel")] = "",
    debug: Annotated[
        bool,
        typer.Option(
            help="Enable debugging.", rich_help_panel="Customization and Utils"
        ),
    ] = False,
    userdata_relpath: Annotated[Path, typer.Option(help="Userdata file (path relative to run.py script)")] = Path('../worker-userdata.yaml'),
):
    user_data_template = Path(__file__).parent / userdata_relpath
    exit_code: int = start_nb_worker(
        user_data_template,
        kernel_id,
        port_range,
        response_address,
        public_key,
        kernel_class_name,
        debug
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    typer.run(main)
