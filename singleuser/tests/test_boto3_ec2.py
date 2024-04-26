import boto3
import pytest


@pytest.fixture
def client():
    client = boto3.client("ec2")
    yield client


def test_describe_instances(client):
    resp = client.describe_instances()
    resis = resp["Reservations"]
    assert resis
    breakpoint()


def test_query_by_tag(client):
    filter = [
        {"Name": "tag:wbn_user", "Values": ["ethho", "fake_user"]},
        # AND logic for filters
        {"Name": "tag:wbn_project", "Values": ["map_ephys"]},
    ]
    resp = client.describe_instances(Filters=filter)
    resis = resp["Reservations"]
    assert resis
    breakpoint()


def test_query_by_instance_id(client):
    instance_id = "my_instance_id"
    resp = client.describe_instances(InstanceIds=[instance_id])
    breakpoint()
