from typing import Optional
from pathlib import Path
import boto3
import botocore
import traceback
from dataclasses import dataclass, asdict
from pprint import pprint
import logging
logging.basicConfig(level=logging.INFO)


@dataclass
class DJHubFetcherResponse:
    """
    """
    name: str
    ami: str
    instance_type: str
    availability_zone: str
    subnet_id: str
    vpc_security_group_ids: str
    # TODO: enable_volume_tags
    # TODO: root block device

    # UserData
    repo_name: str

def start_nb_worker(
    kernel_id: str = "",
    port_range: str = "",
    response_address: str = "",
    public_key: str = "",
    kernel_class_name: str = "",
    userdata_path: Optional[Path] = None,
    debug: bool = False,
    dry_run: bool = True,
    enable_monitoring: bool = False,
    **boto3_kwargs
):
    """
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/run_instances.html

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
    # TODO: get DJHubFetcherResponse
    # TODO: template UserData

    client = boto3.resource('ec2')
    # TODO: choose VPC
    # TODO: choose security group

    try:
        response = client.create_instances(
            # TODO: check that AssociatePublicIpAddress is on by default
            # TODO
            # SubnetId='string',
            DryRun=dry_run,
            # TODO: need to specify AZ?
            # TODO
            MinCount=1,
            MaxCount=1,
            # TODO: AMI
            ImageId='ami-xxxxxxxxxxxxxxxxx',
            # TODO
            Monitoring={'Enabled': enable_monitoring},
            # TODO
            InstanceType='t2.micro',

            EbsOptimized=False,
            BlockDeviceMappings=[
                {
                    "DeviceName": "/dev/sda1",
                    "Ebs": {
                        "Encrypted": False,
                        "DeleteOnTermination": True,
                        # "SnapshotId": "snap-xxxxxxxxxxxxxxxxx",
                        "VolumeSize": 55, # GB
                        "VolumeType": "gp2"
                    }
                }
            ],
            NetworkInterfaces=[
                {
                    "SubnetId": "subnet-xxxxxxxxxxxxxxxxx",
                    "AssociatePublicIpAddress": True,
                    "DeviceIndex": 0,
                    "Groups": [
                        "sg-xxxxxxxxxxxxxxxxx"
                    ]
                }
            ],
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": "djlabhub-wbn-worker-test"
                        }
                    ]
                }
            ],
            PrivateDnsNameOptions={
                "HostnameType": "ip-name",
                "EnableResourceNameDnsARecord": False,
                "EnableResourceNameDnsAAAARecord": False
            },
            # TODO
            # SecurityGroupIds=[
            #     'string',
            # ],
            # SecurityGroups=[
            #     'string',
            # ],
            # TODO
            UserData='string',
            # TODO: needed for UserData?
            # see https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html#user-data-shell-scripts
            # IamInstanceProfile={
            #     'Arn': 'string',
            #     'Name': 'string'
            # },
            # TODO: relevant for UserData
            # see https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html
            # MetadataOptions={
            #     'HttpTokens': 'optional'|'required',
            #     'HttpPutResponseHopLimit': 123,
            #     'HttpEndpoint': 'disabled'|'enabled',
            #     'HttpProtocolIpv6': 'disabled'|'enabled',
            #     'InstanceMetadataTags': 'disabled'|'enabled'
            # },
            # TODO
            # BlockDeviceMappings=[
            #     {
            #         'DeviceName': 'string',
            #         'VirtualName': 'string',
            #         'Ebs': {
            #             'DeleteOnTermination': True|False,
            #             'Iops': 123,
            #             'SnapshotId': 'string',
            #             'VolumeSize': 123,
            #             'VolumeType': 'standard'|'io1'|'io2'|'gp2'|'sc1'|'st1'|'gp3',
            #             'KmsKeyId': 'string',
            #             'Throughput': 123,
            #             'OutpostArn': 'string',
            #             'Encrypted': True|False
            #         },
            #         'NoDevice': 'string'
            #     },
            # ],
            # TODO
            # InstanceInitiatedShutdownBehavior='stop'|'terminate',
            # TODO: tag all resources with tag:wbn_kernel_id
            # TagSpecifications=[
            #     {
            #         'ResourceType': 'capacity-reservation'|'client-vpn-endpoint'|'customer-gateway'|'carrier-gateway'|'coip-pool'|'dedicated-host'|'dhcp-options'|'egress-only-internet-gateway'|'elastic-ip'|'elastic-gpu'|'export-image-task'|'export-instance-task'|'fleet'|'fpga-image'|'host-reservation'|'image'|'import-image-task'|'import-snapshot-task'|'instance'|'instance-event-window'|'internet-gateway'|'ipam'|'ipam-pool'|'ipam-scope'|'ipv4pool-ec2'|'ipv6pool-ec2'|'key-pair'|'launch-template'|'local-gateway'|'local-gateway-route-table'|'local-gateway-virtual-interface'|'local-gateway-virtual-interface-group'|'local-gateway-route-table-vpc-association'|'local-gateway-route-table-virtual-interface-group-association'|'natgateway'|'network-acl'|'network-interface'|'network-insights-analysis'|'network-insights-path'|'network-insights-access-scope'|'network-insights-access-scope-analysis'|'placement-group'|'prefix-list'|'replace-root-volume-task'|'reserved-instances'|'route-table'|'security-group'|'security-group-rule'|'snapshot'|'spot-fleet-request'|'spot-instances-request'|'subnet'|'subnet-cidr-reservation'|'traffic-mirror-filter'|'traffic-mirror-session'|'traffic-mirror-target'|'transit-gateway'|'transit-gateway-attachment'|'transit-gateway-connect-peer'|'transit-gateway-multicast-domain'|'transit-gateway-policy-table'|'transit-gateway-route-table'|'transit-gateway-route-table-announcement'|'volume'|'vpc'|'vpc-endpoint'|'vpc-endpoint-connection'|'vpc-endpoint-service'|'vpc-endpoint-service-permission'|'vpc-peering-connection'|'vpn-connection'|'vpn-gateway'|'vpc-flow-log'|'capacity-reservation-fleet'|'traffic-mirror-filter-rule'|'vpc-endpoint-connection-device-type'|'verified-access-instance'|'verified-access-group'|'verified-access-endpoint'|'verified-access-policy'|'verified-access-trust-provider'|'vpn-connection-device-type'|'vpc-block-public-access-exclusion'|'ipam-resource-discovery'|'ipam-resource-discovery-association'|'instance-connect-endpoint',
            #         'Tags': [
            #             {
            #                 'Key': 'string',
            #                 'Value': 'string'
            #             },
            #         ]
            #     },
            # ],
            **boto3_kwargs,

            # ---------------------------- FUTURE ----------------------------------

            # FUTURE: can optionally define a static network interface
            # when launching
            # NetworkInterfaces=[
            #     {
            #         'AssociatePublicIpAddress': True|False,
            #         'DeleteOnTermination': True|False,
            #         'Description': 'string',
            #         'DeviceIndex': 123,
            #         'Groups': [
            #             'string',
            #         ],
            #         'Ipv6AddressCount': 123,
            #         'Ipv6Addresses': [
            #             {
            #                 'Ipv6Address': 'string',
            #                 'IsPrimaryIpv6': True|False
            #             },
            #         ],
            #         'NetworkInterfaceId': 'string',
            #         'PrivateIpAddress': 'string',
            #         'PrivateIpAddresses': [
            #             {
            #                 'Primary': True|False,
            #                 'PrivateIpAddress': 'string'
            #             },
            #         ],
            #         'SecondaryPrivateIpAddressCount': 123,
            #         'SubnetId': 'string',
            #         'AssociateCarrierIpAddress': True|False,
            #         'InterfaceType': 'string',
            #         'NetworkCardIndex': 123,
            #         'Ipv4Prefixes': [
            #             {
            #                 'Ipv4Prefix': 'string'
            #             },
            #         ],
            #         'Ipv4PrefixCount': 123,
            #         'Ipv6Prefixes': [
            #             {
            #                 'Ipv6Prefix': 'string'
            #             },
            #         ],
            #         'Ipv6PrefixCount': 123,
            #         'PrimaryIpv6': True|False,
            #         'EnaSrdSpecification': {
            #             'EnaSrdEnabled': True|False,
            #             'EnaSrdUdpSpecification': {
            #                 'EnaSrdUdpEnabled': True|False
            #             }
            #         },
            #         'ConnectionTrackingSpecification': {
            #             'TcpEstablishedTimeout': 123,
            #             'UdpStreamTimeout': 123,
            #             'UdpTimeout': 123
            #         }
            #     },
            # ],
            # PrivateIpAddress='string',

            # LaunchTemplate={
            #     'LaunchTemplateId': 'string',
            #     'LaunchTemplateName': 'string',
            #     'Version': 'string'
            # },
            # FUTURE: Possibly interesting to use spot
            # InstanceMarketOptions={
            #     'MarketType': 'spot'|'capacity-block',
            #     'SpotOptions': {
            #         'MaxPrice': 'string',
            #         'SpotInstanceType': 'one-time'|'persistent',
            #         'BlockDurationMinutes': 123,
            #         'ValidUntil': datetime(2015, 1, 1),
            #         'InstanceInterruptionBehavior': 'hibernate'|'stop'|'terminate'
            #     }
            # },
            # FUTURE: for spot instances
            # HibernationOptions={
            #     'Configured': True|False
            # },
            # FUTURE: see https://www.mathworks.com/help/cloudcenter/ug/run-license-manager-using-amazon-web-services.html
            # LicenseSpecifications=[
            #     {
            #         'LicenseConfigurationArn': 'string'
            #     },
            # ],
        )
    except botocore.exceptions.ClientError as e:
        if e.response.get('Error', {}).get('Code') == 'DryRunOperation':
            # DryRunOperation: Request would have succeeded, but DryRun flag is set.
            logging.info("Dry run succeeded")
            return 0
        logging.error("Exception raised with traceback:\n\n" + traceback.format_exc())
        return 1
    else:
        pprint(response)
    return 0

"""
TODO: adapt to
Example body created from AWS console:

{
  "MaxCount": 1,
  "MinCount": 1,
  "ImageId": "ami-xxxxxxxxxxxxxxxxx",
  "InstanceType": "t2.micro",
  "EbsOptimized": false,
  "UserData": "dGhpcyBpcyBteSB1c2VyX2RhdGE=", # "this is my user_data"
  "BlockDeviceMappings": [
    {
      "DeviceName": "/dev/sda1",
      "Ebs": {
        "Encrypted": false,
        "DeleteOnTermination": true,
        "SnapshotId": "snap-xxxxxxxxxxxxxxxxx",
        "VolumeSize": 55,
        "VolumeType": "gp2"
      }
    }
  ],
  "NetworkInterfaces": [
    {
      "SubnetId": "subnet-xxxxxxxxxxxxxxxxx",
      "AssociatePublicIpAddress": true,
      "DeviceIndex": 0,
      "Groups": [
        "sg-xxxxxxxxxxxxxxxxx"
      ]
    }
  ],
  "TagSpecifications": [
    {
      "ResourceType": "instance",
      "Tags": [
        {
          "Key": "Name",
          "Value": "djlabhub-wbn-worker-test"
        },
        {
          "Key": "wbn_kernel_id",
          "Value": "my_kernel_id"
        },
        {
          "Key": "WorkerType",
          "Value": "dev:standardworker:stable"
        }
      ]
    },
    {
      "ResourceType": "volume",
      "Tags": [
        {
          "Key": "wbn_kernel_id",
          "Value": "my_kernel_id"
        },
        {
          "Key": "WorkerType",
          "Value": "dev:standardworker:stable"
        }
      ]
    },
    {
      "ResourceType": "network-interface",
      "Tags": [
        {
          "Key": "wbn_kernel_id",
          "Value": "my_kernel_id"
        },
        {
          "Key": "WorkerType",
          "Value": "dev:standardworker:stable"
        }
      ]
    }
  ],
  "PrivateDnsNameOptions": {
    "HostnameType": "ip-name",
    "EnableResourceNameDnsARecord": false,
    "EnableResourceNameDnsAAAARecord": false
  }
}
"""