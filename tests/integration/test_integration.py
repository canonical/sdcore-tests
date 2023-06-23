#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

import pytest
from fixtures import configure_sdcore, deploy_gnbsim
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


class TestSDCoreBundle:
    @pytest.mark.abort_on_fail
    async def test_given_sdcore_bundle_when_deploy_then_status_is_active(self, ops_test: OpsTest):
        await self._deploy_sdcore(ops_test)
        apps = [*ops_test.model.applications]  # type: ignore[union-attr]
        apps.remove("grafana-agent-k8s")
        await ops_test.model.wait_for_idle(  # type: ignore[union-attr]
            apps=apps,
            raise_on_error=False,
            status="active",
            idle_period=30,
            timeout=1200,
        )

    @pytest.mark.abort_on_fail
    async def test_given_sdcore_bundle_and_gnbsim_deployed_when_start_simulation_then_simulation_success_status_is_true(  # noqa: E501
        self, ops_test: OpsTest, deploy_gnbsim
    ):
        gnbsim_unit = ops_test.model.units["gnbsim/0"]  # type: ignore[union-attr]
        start_simulation = await gnbsim_unit.run_action("start-simulation")
        action_output = await ops_test.model.get_action_output(  # type: ignore[union-attr]
            action_uuid=start_simulation.entity_id, wait=240
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
            idle_period=30,
            timeout=300,
        )
