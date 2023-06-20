#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import os

import pytest
import requests
from jinja2 import Environment, FileSystemLoader
from pytest_operator.plugin import OpsTest

os.environ["KUBECONFIG"] = "/var/snap/microk8s/current/credentials/client.config"

COS_MODEL_NAME = "cos-lite"
GNBSIM_MODEL_NAME = "simulator"
TEST_DEVICE_GROUP_NAME = "integration_tests"
TEST_IMSI = "208930100007487"
TEST_NETWORK_SLICE_NAME = "e2e"
JINJA_ENV = Environment(loader=FileSystemLoader("tests/integration/resources"))


@pytest.fixture(scope="module")
@pytest.mark.abort_on_fail
async def deploy_cos(ops_test: OpsTest):
    """Deploys observability model.

    COS model includes:
    - cos-lite bundle
    - cos-configuration-k8s charm providing custom Charmed SD-Core dashboard

    Args:
        ops_test: OpsTest
    """
    await deploy_cos_lite(ops_test)
    await deploy_cos_configuration(ops_test)


@pytest.fixture(scope="module")
@pytest.mark.abort_on_fail
async def configure_sdcore(ops_test: OpsTest):
    """Configures Charmed SD-Core.

    Configuration includes:
    - subscriber creation
    - device group creation
    - network slice creation

    Args:
        ops_test: OpsTest
    """
    webui_ip_address = await get_unit_address(ops_test, "webui", 0)
    create_subscriber_resp = _create_subscriber(webui_ip_address)
    assert create_subscriber_resp.status_code == 201
    create_device_group_resp = _create_device_group(webui_ip_address)
    assert create_device_group_resp.status_code == 200
    create_network_slice_resp = _create_network_slice(webui_ip_address)
    assert create_network_slice_resp.status_code == 200


@pytest.fixture(scope="module")
@pytest.mark.abort_on_fail
async def deploy_gnbsim(ops_test: OpsTest):
    """Deploys `sdcore-gnbsim`.

    Args:
        ops_test: OpsTest
    """
    await ops_test.model.deploy(  # type: ignore[union-attr]
        "sdcore-gnbsim",
        application_name="gnbsim",
        channel="latest/edge",
        trust=True,
    )
    await ops_test.model.add_relation("gnbsim:fiveg-n2", "amf:fiveg-n2")  # type: ignore[union-attr]  # noqa: E501
    await ops_test.model.wait_for_idle(  # type: ignore[union-attr]
        apps=["gnbsim"],
        raise_on_error=False,
        status="active",
        timeout=300,
    )


async def deploy_cos_lite(ops_test: OpsTest):
    """Deploys `cos-lite` bundle.

    Args:
        ops_test: OpsTest
    """
    await ops_test.track_model(
        alias=COS_MODEL_NAME,
        model_name=COS_MODEL_NAME,
        cloud_name=ops_test.cloud_name,
    )

    with ops_test.model_context(COS_MODEL_NAME):
        await ops_test.model.deploy(  # type: ignore[union-attr]
            entity_url="https://charmhub.io/cos-lite",
            trust=True,
        )
        await ops_test.model.wait_for_idle(  # type: ignore[union-attr]
            apps=[*ops_test.model.applications],  # type: ignore[union-attr]
            raise_on_error=False,
            status="active",
            timeout=600,
        )
        await ops_test.model.create_offer(  # type: ignore[union-attr]
            endpoint="prometheus:receive-remote-write",
            offer_name="prometheus",
            application_name="prometheus",
        )


async def deploy_cos_configuration(ops_test: OpsTest):
    """Deploys `cos-configuration-k8s` charm.

    Args:
        ops_test: OpsTest
    """
    with ops_test.model_context(COS_MODEL_NAME):
        await ops_test.model.deploy(  # type: ignore[union-attr]
            "cos-configuration-k8s",
            config={
                "git_repo": "https://github.com/canonical/sdcore-cos-configuration",
                "git_branch": "main",
                "git_depth": 1,
                "grafana_dashboards_path": "grafana_dashboards/sdcore/",
            },
        )
        await ops_test.model.add_relation("cos-configuration-k8s", "grafana")  # type: ignore[union-attr]  # noqa: E501
        await ops_test.model.wait_for_idle(  # type: ignore[union-attr]
            apps=["cos-configuration-k8s"],
            raise_on_error=False,
            status="active",
            timeout=300,
        )


def _create_subscriber(webui_ip: str) -> requests.Response:
    """Creates a subscriber from a template.

    Args:
        webui_ip: IP address of the `webui` application unit

    Returns:
        requests.Response: requests.Response Object
    """
    template = JINJA_ENV.get_template("subscriber.json.j2")
    subscriber_data = template.render(imsi=TEST_IMSI)
    url = f"http://{webui_ip}:5000/api/subscriber/imsi-{TEST_IMSI}"
    return requests.post(url=url, data=subscriber_data)


def _create_device_group(webui_ip: str) -> requests.Response:
    """Creates a device group from a template.

    Args:
        webui_ip: IP address of the `webui` application unit

    Returns:
        requests.Response: requests.Response Object
    """
    template = JINJA_ENV.get_template("device-group.json.j2")
    device_group_json = json.loads(template.render(imsi=TEST_IMSI))
    url = f"http://{webui_ip}:5000/config/v1/device-group/{TEST_DEVICE_GROUP_NAME}"
    return requests.post(url, json=device_group_json)


def _create_network_slice(webui_ip: str) -> requests.Response:
    """Creates a network slice from a template.

    Args:
        webui_ip: IP address of the `webui` application unit

    Returns:
        requests.Response: requests.Response Object
    """
    template = JINJA_ENV.get_template("network-slice.json.j2")
    network_slice_json = json.loads(template.render(device_group_name=TEST_DEVICE_GROUP_NAME))
    url = f"http://{webui_ip}:5000/config/v1/network-slice/{TEST_NETWORK_SLICE_NAME}"
    return requests.post(url, json=network_slice_json)


async def get_unit_address(ops_test: OpsTest, app_name: str, unit_num: int) -> str:
    """Get unit's IP address for any application.

    Args:
        ops_test: OpsTest
        app_name: string name of application
        unit_num: integer number of a juju unit

    Returns:
        str: Unit's IP address
    """
    status = await ops_test.model.get_status()  # type: ignore[union-attr]
    return status["applications"][app_name]["units"][f"{app_name}/{unit_num}"]["address"]
