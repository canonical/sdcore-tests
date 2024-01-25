#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import pytest
from pytest_operator.plugin import OpsTest
from webui_helper import WebUI

COS_MODEL_NAME = "cos-lite"
GNBSIM_MODEL_NAME = "simulator"
TEST_DEVICE_GROUP_NAME = "default-default"
TEST_IMSI = "208930100007487"
TEST_NETWORK_SLICE_NAME = "default"


@pytest.fixture(scope="module")
@pytest.mark.abort_on_fail
async def setup(ops_test: OpsTest):
    """Sets the interval for the `update-status` hook to 1 minute.

    Args:
        ops_test: OpsTest
    """
    await ops_test.model.set_config({"update-status-hook-interval": "1m"})  # type: ignore[union-attr]  # noqa: E501


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
    await _deploy_cos_lite(ops_test)
    await _deploy_cos_configuration(ops_test)


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
    webui_ip_address = await _get_unit_address(ops_test, "webui", 0)
    webui_client = WebUI(webui_ip_address)
    webui_client.create_subscriber(TEST_IMSI)
    webui_client.create_device_group(TEST_DEVICE_GROUP_NAME, [TEST_IMSI])
    webui_client.create_network_slice(TEST_NETWORK_SLICE_NAME, [TEST_DEVICE_GROUP_NAME])


@pytest.fixture(scope="module")
@pytest.mark.abort_on_fail
async def deploy_gnbsim(ops_test: OpsTest, configure_sdcore):
    """Deploys `sdcore-gnbsim-k8s`.

    Args:
        ops_test: OpsTest
        configure_sdcore: `configure_sdcore` fixture
    """
    await ops_test.model.deploy(  # type: ignore[union-attr]
        "sdcore-gnbsim-k8s",
        application_name="gnbsim",
        channel="latest/edge",
        trust=True,
    )
    await ops_test.model.add_relation("gnbsim:fiveg-n2", "amf:fiveg-n2")  # type: ignore[union-attr]  # noqa: E501
    await ops_test.model.add_relation("gnbsim:fiveg_gnb_identity", "nms:fiveg_gnb_identity")  # type: ignore[union-attr]  # noqa: E501
    await ops_test.model.wait_for_idle(  # type: ignore[union-attr]
        apps=["gnbsim"],
        raise_on_error=False,
        status="active",
        idle_period=10,
        timeout=300,
    )


@pytest.fixture(scope="module")
@pytest.mark.abort_on_fail
async def configure_traefik_external_hostname(ops_test: OpsTest) -> None:
    """Configures external hostname for Traefik charm using its external IP and nip.io.

    Args:
        ops_test: OpsTest
    """
    traefik_public_address = await _get_application_public_address(ops_test, "traefik-k8s")
    await ops_test.model.applications["traefik-k8s"].set_config(  # type: ignore[union-attr]
        {"external_hostname": f"{traefik_public_address}.nip.io"}
    )


async def _deploy_cos_lite(ops_test: OpsTest):
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
        # TODO: Remove below workaround and uncomment the proper deployment once
        #       https://github.com/charmed-kubernetes/pytest-operator/issues/116 is fixed.
        deploy_cos_lite_run_args = ["juju", "deploy", "cos-lite", "--trust"]
        retcode, stdout, stderr = await ops_test.run(*deploy_cos_lite_run_args)
        if retcode != 0:
            raise RuntimeError(f"Error: {stderr}")
        # await ops_test.model.deploy(  # type: ignore[union-attr]
        #     entity_url="https://charmhub.io/cos-lite",
        #     trust=True,
        # )
        await ops_test.model.wait_for_idle(  # type: ignore[union-attr]
            apps=[*ops_test.model.applications],  # type: ignore[union-attr]
            raise_on_error=False,
            status="active",
            timeout=1000,
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


async def _deploy_cos_configuration(ops_test: OpsTest):
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


async def _get_application_public_address(ops_test: OpsTest, app_name: str) -> str:
    """Find public address for any application.

    Args:
        ops_test: OpsTest
        app_name: String name of an application

    Returns:
        str: Application's public address
    """
    status = await ops_test.model.get_status()  # type: ignore[union-attr]
    app = status["applications"][app_name]
    return app.public_address


async def _get_unit_address(ops_test: OpsTest, app_name: str, unit_num: int) -> str:
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
