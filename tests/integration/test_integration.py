#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

import pytest
from fixtures import configure_sdcore, deploy_cos, deploy_gnbsim
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


class TestSDCoreBundle:
    @pytest.mark.abort_on_fail
    async def test_given_sdcore_bundle_when_deploy_then_status_is_active(
        self, ops_test: OpsTest, deploy_cos
    ):
        await self._deploy_sdcore(ops_test)
        await ops_test.model.wait_for_idle(  # type: ignore[union-attr]
            apps=[*ops_test.model.applications],  # type: ignore[union-attr]
            raise_on_error=False,
            status="active",
            idle_period=10,
            timeout=1500,
        )
        get_svc_run_args = ["microk8s", "kubectl", "-n", f"{ops_test.model_name}", "get", "svc"]
        retcode, stdout, stderr = await ops_test.run(*get_svc_run_args)
        logger.error("=======================================================================")
        logger.error(stdout)
        logger.error("=======================================================================")
        if retcode != 0:
            raise RuntimeError(f"Error: {stderr}")

    @pytest.mark.abort_on_fail
    async def test_given_sdcore_bundle_and_gnbsim_deployed_when_start_simulation_then_simulation_success_status_is_true(  # noqa: E501
        self, ops_test: OpsTest, deploy_gnbsim
    ):
        logger.error("=====================================================================")
        import os
        for env_name, env_value in os.environ.items():
            logger.error(f"{env_name}: {env_value}")
        logger.error("=====================================================================")
        logger.error("---------------------------------------------------------------------")
        config = await ops_test.model.get_config()
        logger.error(config)
        logger.error("---------------------------------------------------------------------")
        gnbsim_unit = ops_test.model.units["gnbsim/0"]  # type: ignore[union-attr]
        start_simulation = await gnbsim_unit.run_action("start-simulation")
        action_output = await ops_test.model.get_action_output(  # type: ignore[union-attr]
            action_uuid=start_simulation.entity_id, wait=300
        )
        assert action_output["success"] == "true"

    async def _deploy_sdcore(self, ops_test: OpsTest):
        """Deploys `sdcore` bundle.

        Args:
            ops_test: OpsTest
        """
        await self._deploy_sdcore_router(ops_test)
        await ops_test.model.deploy(  # type: ignore[union-attr]
            entity_url="https://charmhub.io/sdcore",
            channel="latest/edge",
            trust=True,
        )

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
        """Deploys `sdcore-router`.

        Args:
            ops_test: OpsTest
        """
        await ops_test.model.deploy(  # type: ignore[union-attr]
            "sdcore-router",
            application_name="router",
            channel="latest/edge",
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
