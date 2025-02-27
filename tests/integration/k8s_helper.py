#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.

import logging

from lightkube.core.client import Client
from lightkube.resources.core_v1 import Service

logger = logging.getLogger(__name__)
lightkube_client = Client()


class KubernetesError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def get_loadbalancer_service_external_ip(service_name, namespace) -> str:
    """Return external IP address of a given LoadBalancer service."""
    try:
        service = lightkube_client.get(Service, name=service_name, namespace=namespace)
        return service.status.loadBalancer.ingress[0].ip
    except Exception as e:
        raise KubernetesError from e
