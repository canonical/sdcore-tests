#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
import json
import logging
from typing import Tuple

import pytest
import requests
from fixtures import (
    COS_MODEL_NAME,
    configure_sdcore,
    configure_traefik_external_hostname,
    deploy_cos,
    deploy_gnbsim,
    setup,
)
from pytest_operator.plugin import OpsTest
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class TestSDCoreBundle:
    @pytest.mark.abort_on_fail
    async def test_given_sdcore_bundle_when_deploy_then_status_is_active(
        self, ops_test: OpsTest, setup, deploy_cos
    ):
        await self._deploy_sdcore(ops_test)
        await ops_test.model.wait_for_idle(  # type: ignore[union-attr]
            apps=[*ops_test.model.applications],  # type: ignore[union-attr]
            raise_on_error=False,
            status="active",
            idle_period=10,
            timeout=1500,
        )

    @pytest.mark.abort_on_fail
    async def test_given_sdcore_bundle_and_gnbsim_deployed_when_start_simulation_then_simulation_success_status_is_true(  # noqa: E501
        self, ops_test: OpsTest, deploy_gnbsim
    ):
        gnbsim_unit = ops_test.model.units["gnbsim/0"]  # type: ignore[union-attr]
        start_simulation = await gnbsim_unit.run_action("start-simulation")
        action_output = await ops_test.model.get_action_output(  # type: ignore[union-attr]
            action_uuid=start_simulation.entity_id, wait=300
        )
        assert action_output["success"] == "true"

    @pytest.mark.abort_on_fail
    async def test_given_external_hostname_configured_for_traefik_when_calling_sdcore_nms_then_configuration_tabs_are_available(  # noqa: E501
        self, ops_test: OpsTest, configure_traefik_external_hostname
    ):
        nms_url = await self._get_nms_url(ops_test)
        network_configuration_resp = requests.get(f"{nms_url}/network-configuration")
        network_configuration_resp.raise_for_status()
        subscribers_resp = requests.get(f"{nms_url}/subscribers")
        subscribers_resp.raise_for_status()

    @pytest.mark.abort_on_fail
    async def test_given_cos_lite_integrated_with_sdcore_when_searching_for_5g_network_overview_dashboard_in_grafana_then_dashboard_exists(  # noqa: E501
        self, ops_test: OpsTest
    ):
        dashboard_name = "5G Network Overview"
        grafana_url, grafana_passwd = await self._get_grafana_url_and_admin_password(ops_test)
        network_overview_dashboard_query = "%20".join(dashboard_name.split())
        request_url = f"{grafana_url}/api/search?query={network_overview_dashboard_query}"
        resp = requests.get(
            url=request_url, auth=HTTPBasicAuth(username="admin", password=grafana_passwd)
        )
        resp.raise_for_status()

    async def _deploy_sdcore(self, ops_test: OpsTest):
        """Deploys `sdcore-k8s` bundle.

        Args:
            ops_test: OpsTest
        """
        await self._deploy_sdcore_router(ops_test)

        # TODO: Remove below workaround and uncomment the proper deployment once
        #       https://github.com/charmed-kubernetes/pytest-operator/issues/116 is fixed.
        deploy_sd_core_run_args = ["juju", "deploy", "sdcore-k8s", "--trust", "--channel=edge"]
        retcode, stdout, stderr = await ops_test.run(*deploy_sd_core_run_args)
        if retcode != 0:
            raise RuntimeError(f"Error: {stderr}")
        # await ops_test.model.deploy(  # type: ignore[union-attr]
        #     entity_url="https://charmhub.io/sdcore",
        #     channel="latest/edge",
        #     trust=True,
        # )

        await self._create_cross_model_relation(
            ops_test,
            provider_model="cos-lite",
            offer_name="prometheus",
            provider_relation_name="receive-remote-write",
            requirer_app="grafana-agent-k8s",
            requirer_relation_name="send-remote-write",
        )
        await self._create_cross_model_relation(
            ops_test,
            provider_model="cos-lite",
            offer_name="loki",
            provider_relation_name="logging",
            requirer_app="grafana-agent-k8s",
            requirer_relation_name="logging-consumer",
        )

    @staticmethod
    async def _deploy_sdcore_router(ops_test: OpsTest):
        """Deploys `sdcore-router-k8s`.

        Args:
            ops_test: OpsTest
        """
        await ops_test.model.deploy(  # type: ignore[union-attr]
            "sdcore-router-k8s",
            application_name="router",
            channel="edge",
            trust=True,
        )
        await ops_test.model.wait_for_idle(  # type: ignore[union-attr]
            apps=["router"],
            raise_on_error=False,
            status="active",
            idle_period=10,
            timeout=300,
        )

    @staticmethod
    async def _create_cross_model_relation(
        ops_test: OpsTest,
        provider_model: str,
        offer_name: str,
        provider_relation_name: str,
        requirer_app: str,
        requirer_relation_name: str,
    ) -> None:
        """Creates a cross-model relation.

        1. Consumes an offer created by the relation provider model
        2. Creates a relation between the provider and the consumer.

        Args:
            ops_test: OpsTest
            provider_model: Provider model name
            offer_name: Relation offer name
            provider_relation_name: Provider relation name
            requirer_app: Requirer application name
            requirer_relation_name: Requirer relation name
        """
        consume_run_args = ["juju", "consume", f"{provider_model}.{offer_name}"]
        retcode, stdout, stderr = await ops_test.run(*consume_run_args)
        if retcode != 0:
            raise RuntimeError(f"Error: {stderr}")
        await ops_test.model.add_relation(  # type: ignore[union-attr]
            f"{offer_name}:{provider_relation_name}", f"{requirer_app}:{requirer_relation_name}"
        )

    @staticmethod
    async def _get_nms_url(ops_test: OpsTest) -> str:
        """Gets the URL of the SD-Core NMS application from Traefik.

        Args:
            ops_test: OpsTest

        Returns:
            str: URL of the SD-Core NMS application
        """
        traefik_unit = ops_test.model.units["traefik-k8s/0"]  # type: ignore[union-attr]
        show_endpoints = await traefik_unit.run_action("show-proxied-endpoints")
        action_output = await ops_test.model.get_action_output(  # type: ignore[union-attr]
            action_uuid=show_endpoints.entity_id, wait=300
        )
        proxied_endpoints = json.loads(action_output["proxied-endpoints"])
        return proxied_endpoints["nms"]["url"]

    @staticmethod
    async def _get_grafana_url_and_admin_password(ops_test: OpsTest) -> Tuple[str, str]:
        """Gets Grafana URL and admin password.

        Args:
            ops_test: OpsTest

        Returns:
            str: Grafana URL
            str: Grafana admin password
        """
        with ops_test.model_context(COS_MODEL_NAME):
            grafana_unit = ops_test.model.units["grafana/0"]  # type: ignore[union-attr]
            get_admin_password = await grafana_unit.run_action("get-admin-password")
            action_output = await ops_test.model.get_action_output(  # type: ignore[union-attr]
                action_uuid=get_admin_password.entity_id, wait=300
            )
        return action_output["url"], action_output["admin-password"]
