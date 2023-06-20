#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

import pytest
from fixtures import configure_sdcore, deploy_cos, deploy_gnbsim, deploy_sdcore
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


class TestSDCoreBundle:
    @pytest.mark.abort_on_fail
    async def test_given_sdcore_bundle_and_cos_lite_bundle_when_deployed_and_related_then_status_is_active(  # noqa: E501
        self, ops_test: OpsTest, deploy_sdcore
    ):
        await ops_test.model.wait_for_idle(  # type: ignore[union-attr]
            apps=[*ops_test.model.applications],  # type: ignore[union-attr]
            raise_on_error=False,
            status="active",
            timeout=1200,
        )

    @pytest.mark.abort_on_fail
    async def test_given_sdcore_bundle_and_cos_lite_bundle_when_deployed_and_related_then(
        self, ops_test: OpsTest, deploy_gnbsim
    ):
        gnbsim_unit = ops_test.model.units["gnbsim/0"]  # type: ignore[union-attr]
        start_simulation = await gnbsim_unit.run_action("start-simulation")
        action_output = await ops_test.model.get_action_output(  # type: ignore[union-attr]
            action_uuid=start_simulation.entity_id, wait=240
        )
        assert action_output["success"] == "true"
