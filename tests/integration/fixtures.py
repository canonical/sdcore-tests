#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import pytest
from pytest_operator.plugin import OpsTest
from webui_helper import WebUI

COS_MODEL_NAME = "cos-lite"
GNBSIM_MODEL_NAME = "simulator"
TEST_DEVICE_GROUP_NAME = "integration_tests"
TEST_IMSI = "208930100007487"
TEST_NETWORK_SLICE_NAME = "e2e"


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

        await _create_cross_model_relation_offer(
            ops_test,
            model_name=COS_MODEL_NAME,
            application_name="loki",
            relation_name="logging",
        )
        await _create_cross_model_relation_offer(
            ops_test,
            model_name=COS_MODEL_NAME,
            application_name="prometheus",
            relation_name="receive-remote-write",
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


async def _create_cross_model_relation_offer(
    ops_test: OpsTest, model_name: str, application_name: str, relation_name: str
) -> None:
    """Creates a cross-model relation offer.

    Args:
        ops_test: OpsTest
        model_name: Provider model name
        application_name: Provider application
        relation_name: Provider relation name
    """
    offer_run_args = ["juju", "offer", f"{model_name}.{application_name}:{relation_name}"]
    retcode, stdout, stderr = await ops_test.run(*offer_run_args)
    if retcode != 0:
        raise RuntimeError(f"Error: {stderr}")
