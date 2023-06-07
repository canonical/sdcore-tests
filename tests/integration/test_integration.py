#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

import pytest
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


COS_MODEL_NAME = "cos-lite"


class TestSDCoreBundle:
    @pytest.fixture(scope="module")
    @pytest.mark.abort_on_fail
    async def setup(self, ops_test: OpsTest):
        await self._deploy_cos_lite(ops_test)
        await self._deploy_sdcore_bundle(ops_test)

    @pytest.mark.abort_on_fail
    async def test_given_sdcore_bundle_and_cos_lite_bundle_when_deployed_and_related_then_status_is_active(  # noqa: E501
        self, ops_test: OpsTest, setup
    ):
        await ops_test.model.wait_for_idle(
            apps=[*ops_test.model.applications],
            raise_on_error=False,
            status="active",
            timeout=1200,
        )

    @staticmethod
    async def _deploy_sdcore_bundle(ops_test: OpsTest):
        """Deploys `sdcore` bundle."""
        await ops_test.model.deploy(
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
        await ops_test.model.add_relation(
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
            logger.error(ops_test.model.name)
            run_args = [
                "juju",
                "deploy",
                "cos-lite",
                "--trust",
            ]
            retcode, stdout, stderr = await ops_test.run(*run_args)
            if retcode != 0:
                raise RuntimeError(f"Error: {stderr}")

            await ops_test.model.wait_for_idle(
                apps=[*ops_test.model.applications],
                raise_on_error=False,
                status="active",
                timeout=1200,
            )

            await ops_test.model.create_offer(
                endpoint="prometheus:receive-remote-write",
                offer_name="prometheus",
                application_name="prometheus",
            )
