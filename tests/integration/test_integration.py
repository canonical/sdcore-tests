#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import logging
import os

import helpers
import pytest
import requests
from jinja2 import Environment, FileSystemLoader
from pytest_operator.plugin import OpsTest
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


COS_MODEL_NAME = "cos-lite"
GNBSIM_MODEL_NAME = "simulator"


class TestSDCoreBundle:
    @pytest.fixture(scope="module")
    @pytest.mark.abort_on_fail
    async def setup(self, ops_test: OpsTest):
        os.environ["KUBECONFIG"] = "/var/snap/microk8s/current/credentials/client.config"
        await self._deploy_sdcore_router(ops_test)
        await self._deploy_gnbsim(ops_test)
        await self._deploy_cos_lite(ops_test)
        await self._deploy_sdcore_bundle(ops_test)

    @pytest.mark.abort_on_fail
    async def test_given_sdcore_bundle_and_cos_lite_bundle_when_deployed_and_related_then_status_is_active(  # noqa: E501
        self, ops_test: OpsTest, setup
    ):
        await ops_test.model.wait_for_idle(  # type: ignore[union-attr]
            apps=[*ops_test.model.applications],  # type: ignore[union-attr]
            status="active",
            timeout=1200,
            idle_period=15,
        )

    @pytest.mark.abort_on_fail
    async def test_given_sdcore_bundle_and_cos_lite_bundle_when_deployed_and_related_then_status_is_configured(  # noqa: E501
        self, ops_test: OpsTest, setup
    ):
        await self._configure_sdcore(ops_test)
        await self._configure_grafana_dashboards(ops_test)

    @staticmethod
    async def _deploy_sdcore_bundle(ops_test: OpsTest):
        """Deploys `sdcore` bundle."""
        await ops_test.model.deploy(  # type: ignore[union-attr]
            entity_url="https://charmhub.io/sdcore",
            channel="latest/edge",
            trust=True,
        )

        run_args_consume = [
            "juju",
            "consume",
            "cos-lite.prometheus",
        ]
        retcode, stdout, stderr = await ops_test.run(*run_args_consume)
        if retcode != 0:
            raise RuntimeError(f"Error: {stderr}")
        await ops_test.model.add_relation(  # type: ignore[union-attr]
            "prometheus:receive-remote-write", "grafana-agent-k8s:send-remote-write"
        )

    @staticmethod
    async def _deploy_cos_lite(ops_test: OpsTest):
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
                timeout=1200,
            )
            await ops_test.model.create_offer(  # type: ignore[union-attr]
                endpoint="prometheus:receive-remote-write",
                offer_name="prometheus",
                application_name="prometheus",
            )

    @staticmethod
    async def _deploy_gnbsim(ops_test: OpsTest):
        await ops_test.model.deploy(  # type: ignore[union-attr]
            "sdcore-gnbsim",
            channel="latest/edge",
            trust=True,
        )
        await ops_test.model.wait_for_idle(  # type: ignore[union-attr]
            apps=["sdcore-gnbsim"],
            raise_on_error=False,
            status="active",
            timeout=300,
        )

    @staticmethod
    async def _deploy_sdcore_router(ops_test: OpsTest):
        await ops_test.model.deploy(  # type: ignore[union-attr]
            "sdcore-router",
            channel="latest/edge",
            trust=True,
        )
        await ops_test.model.wait_for_idle(  # type: ignore[union-attr]
            apps=["sdcore-router"],
            raise_on_error=False,
            status="active",
            timeout=300,
        )

    @staticmethod
    async def _configure_sdcore(ops_test: OpsTest):
        webui_ip_address = await helpers.get_unit_address(ops_test, "webui", 0)
        create_subscriber_resp = _create_subscriber(webui_ip_address)
        assert create_subscriber_resp.status_code == 201
        create_device_group_resp = _create_device_group(webui_ip_address, "test_device_group")
        assert create_device_group_resp.status_code == 200
        create_network_slice_resp = _create_network_slice(webui_ip_address, "default")
        assert create_network_slice_resp.status_code == 200

    async def _configure_grafana_dashboards(self, ops_test: OpsTest):
        grafana_external_ip = helpers.get_load_balancer_service_external_ip(
            COS_MODEL_NAME,
            "traefik",
        )
        grafana_base_url = f"https://{grafana_external_ip}/{COS_MODEL_NAME}-grafana"
        grafana_admin_password = await self._get_grafana_admin_password(ops_test)
        prometheus_ds_uid = _get_prometheus_datasource_uid(
            grafana_url=grafana_base_url,
            user="admin",
            password=grafana_admin_password,
        )
        grafana_dashboard_config = _render_grafana_dashboard_config(prometheus_ds_uid)
        resp = requests.post(
            f"{grafana_base_url}/api/dashboards/db",
            auth=HTTPBasicAuth("admin", grafana_admin_password),
            json=grafana_dashboard_config,
            verify=False,
        )
        assert resp.status_code == 200
        logger.error("=======================================================================")
        logger.error(resp.json())
        import time

        time.sleep(300)

    @staticmethod
    async def _get_grafana_admin_password(ops_test: OpsTest) -> str:
        with ops_test.model_context(COS_MODEL_NAME):
            grafana_unit = ops_test.model.units["grafana/0"]  # type: ignore[union-attr]
            get_admin_password_action = await grafana_unit.run_action("get-admin-password")
            action_output = await ops_test.model.get_action_output(  # type: ignore[union-attr]
                action_uuid=get_admin_password_action.entity_id, wait=240
            )
            return action_output["admin-password"]


def _create_subscriber(webui_ip: str) -> requests.Response:
    with open("tests/integration/resources/subscriber.json") as subscriber_file:
        subscriber_json = subscriber_file.read()
    imsi = json.loads(subscriber_json)["UeId"]
    url = f"http://{webui_ip}:5000/api/subscriber/imsi-{imsi}"
    return requests.post(url, data=subscriber_json)


def _create_device_group(webui_ip: str, device_group_name: str) -> requests.Response:
    with open("tests/integration/resources/device-group.json") as device_group_file:
        device_group_json = device_group_file.read()
    url = f"http://{webui_ip}:5000/config/v1/device-group/{device_group_name}"
    return requests.post(url, data=device_group_json)


def _create_network_slice(webui_ip: str, network_slice_name: str) -> requests.Response:
    with open("tests/integration/resources/network-slice.json") as network_slice_file:
        network_slice_json = network_slice_file.read()
    url = f"http://{webui_ip}:5000/config/v1/network-slice/{network_slice_name}"
    return requests.post(url, data=network_slice_json)


def _get_prometheus_datasource_uid(grafana_url: str, user: str, password: str) -> str:
    grafana_datasources = helpers.get_grafana_datasources(
        grafana_url=grafana_url,
        user=user,
        password=password,
    )
    return helpers.get_grafana_datasource_uid("prometheus", grafana_datasources)


def _render_grafana_dashboard_config(prometheus_ds_uid: str) -> str:
    jinja2_env = Environment(loader=FileSystemLoader("tests/integration/resources"))
    template = jinja2_env.get_template("grafana-dashboard.json.j2")
    return json.loads(template.render(prometheus_datasource_id=prometheus_ds_uid))
