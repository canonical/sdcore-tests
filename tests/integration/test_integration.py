#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import logging
import os
import time
from typing import Tuple

import pytest
import requests
from jinja2 import Environment, FileSystemLoader
from requests.auth import HTTPBasicAuth

from tests.integration import juju_helper
from tests.integration.nms_helper import Nms
from tests.integration.terraform_helper import TerraformClient

logger = logging.getLogger(__name__)

SDCORE_MODEL_NAME = "sdcore"
COS_MODEL_NAME = "cos-lite"
TERRAFORM_DIR = "terraform"
TFVARS_FILE = "integration_tests.auto.tfvars"
TEST_DEVICE_GROUP_NAME = "default-default"
TEST_IMSI = "208930100007487"
TEST_NETWORK_SLICE_NAME = "default"


class TestSDCoreBundle:
    @classmethod
    def setup_class(cls):
        juju_helper.set_model_config(
            model_name=SDCORE_MODEL_NAME,
            config={"update-status-hook-interval": "1m"},
        )

    @pytest.mark.abort_on_fail
    async def test_given_sdcore_terraform_module_when_deploy_then_status_is_active(self):
        self._deploy_sdcore()
        juju_helper.juju_wait_for_active_idle(model_name=SDCORE_MODEL_NAME, timeout=1200)

    @pytest.mark.abort_on_fail
    async def test_given_sdcore_bundle_and_gnbsim_deployed_when_start_simulation_then_simulation_success_status_is_true(  # noqa: E501
        self, configure_sdcore
    ):
        for _ in range(5):
            action_output = juju_helper.juju_run_action(
                model_name=SDCORE_MODEL_NAME,
                application_name="gnbsim",
                unit_number=0,
                action_name="start-simulation",
                timeout=6 * 60,
            )
            try:
                assert action_output["success"] == "true"
                return
            except AssertionError:
                continue
        assert False

    @pytest.mark.skip(
        reason="Traefik issue: https://github.com/canonical/traefik-k8s-operator/issues/361"
    )
    @pytest.mark.abort_on_fail
    async def test_given_external_hostname_configured_for_traefik_when_calling_sdcore_nms_then_configuration_tabs_are_available(  # noqa: E501
        self, configure_traefik_external_hostname
    ):
        nms_url = self._get_nms_url()
        network_configuration_resp = requests.get(f"{nms_url}/network-configuration")
        network_configuration_resp.raise_for_status()
        subscribers_resp = requests.get(f"{nms_url}/subscribers")
        subscribers_resp.raise_for_status()

    @pytest.mark.abort_on_fail
    async def test_given_cos_lite_integrated_with_sdcore_when_searching_for_5g_network_overview_dashboard_in_grafana_then_dashboard_exists(  # noqa: E501
        self,
    ):
        dashboard_name = "5G Network Overview"
        grafana_url, grafana_passwd = await self._get_grafana_url_and_admin_password()
        network_overview_dashboard_query = "%20".join(dashboard_name.split())
        request_url = f"{grafana_url}/api/search?query={network_overview_dashboard_query}"
        resp = requests.get(
            url=request_url, auth=HTTPBasicAuth(username="admin", password=grafana_passwd)
        )
        resp.raise_for_status()

    def _deploy_sdcore(self):
        """Deploy the SD-Core Terraform module for testing.

        SD-Core Terraform module contains:
        - sdcore-k8s Terraform module
        - cos-lite Terraform module
        - sdcore-router-k8s Terraform module
        - sdcore-gnbsim-k8s Terraform module
        """
        self._generate_tfvars_file()
        tf_client = TerraformClient(work_dir=os.path.join(os.getcwd(), TERRAFORM_DIR))
        tf_client.init()
        tf_client.apply()

    @staticmethod
    def _generate_tfvars_file():
        """Generate .tfvars file to configure Terraform deployment."""
        jinja2_environment = Environment(loader=FileSystemLoader(f"{TERRAFORM_DIR}/"))
        template = jinja2_environment.get_template(f"{TFVARS_FILE}.j2")
        content = template.render(
            sdcore_model_name=SDCORE_MODEL_NAME,
            cos_model_name=COS_MODEL_NAME,
        )
        with open(f"{TERRAFORM_DIR}/{TFVARS_FILE}", mode="w") as tfvars:
            tfvars.write(content)

    @staticmethod
    def _get_nms_url() -> str:
        """Get the URL of the SD-Core NMS application from Traefik.

        Returns:
            str: URL of the SD-Core NMS application
        """
        action_output = juju_helper.juju_run_action(
            model_name=SDCORE_MODEL_NAME,
            application_name="traefik",
            unit_number=0,
            action_name="show-proxied-endpoints",
        )
        proxied_endpoints = json.loads(action_output["proxied-endpoints"])
        return proxied_endpoints["nms"]["url"]

    @staticmethod
    async def _get_grafana_url_and_admin_password() -> Tuple[str, str]:
        """Get Grafana URL and admin password.

        Returns:
            str: Grafana URL
            str: Grafana admin password
        """
        action_output = juju_helper.juju_run_action(
            model_name=COS_MODEL_NAME,
            application_name="grafana",
            unit_number=0,
            action_name="get-admin-password",
        )
        return action_output["url"], action_output["admin-password"]


@pytest.fixture(scope="module")
@pytest.mark.abort_on_fail
def configure_sdcore():
    """Configure Charmed SD-Core.

    Configuration includes:
    - subscriber creation
    - device group creation
    - network slice creation
    """
    nms_ip_address = juju_helper.get_unit_address(
        model_name=SDCORE_MODEL_NAME,
        application_name="nms",
        unit_number=0,
    )
    nms_client = Nms(nms_ip_address)
    nms_client.create_subscriber(TEST_IMSI)
    nms_client.create_device_group(TEST_DEVICE_GROUP_NAME, [TEST_IMSI])
    nms_client.create_network_slice(TEST_NETWORK_SLICE_NAME, [TEST_DEVICE_GROUP_NAME])
    # 5 seconds for the config to propagate
    time.sleep(5)


@pytest.fixture(scope="module")
@pytest.mark.abort_on_fail
def configure_traefik_external_hostname() -> None:
    """Configure external hostname for Traefik charm using its external IP and nip.io."""
    traefik_public_address = juju_helper.get_application_address(
        model_name=SDCORE_MODEL_NAME,
        application_name="traefik",
    )
    juju_helper.set_application_config(
        model_name=SDCORE_MODEL_NAME,
        application_name="traefik",
        config={"external_hostname": f"{traefik_public_address}.nip.io"},
    )
