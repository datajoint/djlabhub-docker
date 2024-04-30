from setuptools import setup

setup(
    name="jupyter_ec2_provisioner",
    version="0.1.0",
    description="Jupyter EC2 kernel provisioner",
    url="",
    author="",
    author_email="",
    license="MIT",
    packages=["jupyter_ec2_provisioner"],
    install_requires=[
        "jupyter_client>=7.1.2",
        "typer>=0.12.3",
        "boto3>=1.34.00",
    ],
    long_description="",
    entry_points={
        "jupyter_client.kernel_provisioners": [
            "ec2-provisioner = jupyter_ec2_provisioner:EC2Provisioner",
        ]
    },
    scripts=[],
    include_package_data=True,
)