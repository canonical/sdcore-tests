#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import pytest
from pytest_operator.plugin import OpsTest


@pytest.fixture(scope="module")
@pytest.mark.abort_on_fail
async def deploy_sdcore_bundle(ops_test: OpsTest):
    """Deploys `sdcore` bundle."""
    run_args = [
        "juju",
        "deploy",
        "sdcore",
        "--trust",
        "--channel=edge",
    ]
    retcode, stdout, stderr = await ops_test.run(*run_args)
    if retcode != 0:
        raise RuntimeError(f"Error: {stderr}")
    # await ops_test.model.deploy(entity_url="https://charmhub.io/sdcore", channel="latest/edge", trust=True)


@pytest.mark.abort_on_fail
async def test_given_charm_is_built_when_deployed_then_status_is_active(
    ops_test,
    deploy_sdcore_bundle,
):
    await ops_test.model.wait_for_idle(
        apps=["upf"],
        raise_on_error=False,
        status="active",
        timeout=1200,
    )
