#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.

import logging
from typing import Optional

from lightkube.core.client import Client
from lightkube.core.exceptions import ApiError
from lightkube.resources.core_v1 import Service

logger = logging.getLogger(__name__)


class KubernetesError(Exception):
    pass


def get_loadbalancer_service_external_ip(service_name, namespace) -> Optional[str]:
    """Return external IP address of a given LoadBalancer service."""
    try:
        lightkube_client = Client()
        service = lightkube_client.get(Service, name=service_name, namespace=namespace)
    except ApiError as e:
        raise KubernetesError() from e

    if not (status := getattr(service, "status", None)):
        raise KubernetesError("Unable to get status of service %s", service_name)
    if not (load_balancer_status := getattr(status, "loadBalancer", None)):
        raise KubernetesError("Unable to get LoadBalancer status for service %s", service_name)
    if not (ingress_addresses := getattr(load_balancer_status, "ingress", None)):
        raise KubernetesError("Unable to get Ingress for service %s", service_name)
    if not (ingress_address := ingress_addresses[0]):
        raise KubernetesError("Unable to get Ingress address for service %s", service_name)

    return ingress_address.ip
