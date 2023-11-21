#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import random

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
    async def test_chaos(self, ops_test: OpsTest, deploy_gnbsim):
        gnbsim_unit = ops_test.model.units["gnbsim/0"]  # type: ignore[union-attr]

        network_functions = [
            "amf-0",
            "ausf-0",
            "nrf-0",
            "nssf-0",
            "pcf-0",
            "smf-0",
            "udm-0",
            "udr-0",
            "webui-0",
        ]
        successes = list()
        while True:
            nf = random.choice(network_functions)
            logger.info("Chaos victim: %s", nf)
            delete_pod = [
                "microk8s.kubectl",
                "delete",
                "pod",
                "-n",
                ops_test.model.name,
                nf,
            ]
            retcode, stdout, stderr = await ops_test.run(*delete_pod)
            if retcode != 0:
                raise RuntimeError(f"Error: {stderr}")

            await ops_test.model.wait_for_idle(  # type: ignore[union-attr]
                apps=[*ops_test.model.applications],  # type: ignore[union-attr]
                raise_on_error=False,
                status="active",
                idle_period=10,
                timeout=1500,
            )

            start_simulation = await gnbsim_unit.run_action("start-simulation")
            action_output = await ops_test.model.get_action_output(  # type: ignore[union-attr]
                action_uuid=start_simulation.entity_id, wait=300
            )
            if action_output.get("success", "false") != "true":
                logger.error("Failed after deleting %s", nf)
                logger.error("Successes:\n%s\n", successes)
                system.exit(1)
            else:
                successes.append(nf)
                logger.info("Successes so far:\n%s\n", successes)

    async def _deploy_sdcore(self, ops_test: OpsTest):
        """Deploys `sdcore` bundle.

        Args:
            ops_test: OpsTest
        """
        await self._deploy_sdcore_router(ops_test)

        # TODO: Remove below workaround and uncomment the proper deployment once
        #       https://github.com/charmed-kubernetes/pytest-operator/issues/116 is fixed.
        deploy_sd_core_run_args = ["juju", "deploy", "sdcore", "--trust", "--channel=edge"]
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
