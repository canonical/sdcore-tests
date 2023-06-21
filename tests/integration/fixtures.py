#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import pytest
from pytest_operator.plugin import OpsTest
from webui_helper import WebUI

GNBSIM_MODEL_NAME = "simulator"
TEST_DEVICE_GROUP_NAME = "integration_tests"
TEST_IMSI = "208930100007487"
TEST_NETWORK_SLICE_NAME = "e2e"


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
    webui_client = WebUI(webui_ip_address)
    webui_client.create_subscriber(TEST_IMSI)
    webui_client.create_device_group(TEST_DEVICE_GROUP_NAME, [TEST_IMSI])
    webui_client.create_network_slice(TEST_NETWORK_SLICE_NAME, [TEST_DEVICE_GROUP_NAME])


@pytest.fixture(scope="module")
@pytest.mark.abort_on_fail
async def deploy_gnbsim(ops_test: OpsTest, configure_sdcore):
    """Deploys `sdcore-gnbsim`.

    Args:
        ops_test: OpsTest
        configure_sdcore: `configure_sdcore` fixture
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
        idle_period=10,
        timeout=300,
    )


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
