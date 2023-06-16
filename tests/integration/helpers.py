#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

import requests
from lightkube import Client
from lightkube.resources.core_v1 import Service
from pytest_operator.plugin import OpsTest
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


async def get_unit_address(ops_test: OpsTest, app_name: str, unit_num: int) -> str:
    """Get unit's IP address for any application.

    Args:
        ops_test: pytest-operator plugin
        app_name: string name of application
        unit_num: integer number of a juju unit

    Returns:
        str: Unit's IP address
    """
    status = await ops_test.model.get_status()  # type: ignore[union-attr]
    return status["applications"][app_name]["units"][f"{app_name}/{unit_num}"]["address"]


def get_load_balancer_service_external_ip(namespace: str, service_name: str) -> str:
    k8s_client = Client()
    services_list = k8s_client.list(res=Service, namespace=namespace)
    for service in services_list:
        if service.metadata.name == service_name:
            return service.status.loadBalancer.ingress[0].ip


def get_grafana_datasources(grafana_url: str, user: str, password: str) -> dict:
    return requests.get(
        f"{grafana_url}/api/datasources",
        auth=HTTPBasicAuth(user, password),
        verify=False,
    ).json()


def get_grafana_datasource_uid(datasource_type: str, datasources: dict) -> str:
    for datasource in datasources:
        if datasource["type"] == datasource_type:
            return datasource["uid"]
