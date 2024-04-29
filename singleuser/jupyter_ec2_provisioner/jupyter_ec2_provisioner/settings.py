from typing import Any, Callable, Set, List
from pydantic import (
    AliasChoices,
    AmqpDsn,
    BaseModel,
    Field,
    ImportString,
    PostgresDsn,
    RedisDsn,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


"""
    name                        = each.value.instance_name
    ami                         = each.value.ami
    instance_type               = each.value.instance_type
    monitoring                  = false
    availability_zone           = "${var.region}${var.az_suffix}"
    vpc_security_group_ids      = var.vpc_security_group_ids
    subnet_id                   = var.subnet_id
    associate_public_ip_address = true

    enable_volume_tags = false
    root_block_device = [{
        encrypted             = true
        delete_on_termination = true
        volume_type           = each.value.root_type
        volume_size           = each.value.root_size
        tags = merge(local.tags, {
        Name = "${each.value.instance_name}.root"
        })
    }]

    user_data = templatefile("${path.root}/shared/worker-userdata.yaml",
        merge({
        ORG_NAME              = var.org_name
        WORKFLOW_NAME         = var.workflow_name
        REPO_NAME             = var.repo_name
        BUCKET_NAME           = var.bucket_name
        EFS_ID                = var.efs_id
        EFS_AP_ID             = var.efs_ap_id
        WORKER_CONTAINER_UID  = each.value.uid
        WORKER_CONTAINER_GID  = each.value.gid
        IF_PULL_IMAGE         = each.value.if_pull_image
        DOCKER_HOST           = "${each.value.if_pull_image}" == "False" ? "" : "${var.docker_host}"
        DOCKER_USERNAME       = "${each.value.if_pull_image}" == "False" ? "" : "${var.docker_username}"
        DOCKER_PASSWORD       = "${each.value.if_pull_image}" == "False" ? "" : "${var.docker_password}"
        WORKFLOW_IMAGE        = "${each.value.if_pull_image}" == "False" ? "" : "${each.value.image_name}:${each.value.image_version}"
        MATLAB_LICENSE_BASE64 = each.value.matlab_license_base64
        ENV_FILE              = filebase64("${path.root}/inputs/${var.org_name}_${var.workflow_name}/env/${each.value.worker_name}.env")
        WORKER_DOCKER_SUBDIR  = each.value.worker_name
        DD_API_KEY            = var.dd_api_key
        SCOPE                 = local.tags.Scope
        CONTRACT              = local.tags.Contract
"""

class Settings(BaseSettings):
	vpc_security_group_id: str
	subnet_id: str

	monitoring: bool = False
	availability_zone: str = 'us-east-2'
	# TODO: use AWS_REGION
	associate_public_ip_address: bool = True
	enable_volume_tags: bool = False
	default_ami: str = 'ami-0a3a99be3bdbef1f6'
	default_instance_type: str = 't2.micro'

settings = Settings(_env_file='.env')
