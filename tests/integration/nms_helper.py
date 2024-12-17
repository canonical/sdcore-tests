#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Module use to handle NMS API calls."""

import json
import logging
import time
from dataclasses import asdict, dataclass
from typing import Any, List, Optional

import requests

logger = logging.getLogger(__name__)

ACCOUNTS_URL = "config/v1/account"

JSON_HEADER = {"Content-Type": "application/json"}

SUBSCRIBER_CONFIG = {
    "UeId": "PLACEHOLDER",
    "plmnId": "00101",
    "opc": "981d464c7c52eb6e5036234984ad0bcf",
    "key": "5122250214c33e723a5dd523fc145fc0",
    "sequenceNumber": "16f3b3f70fc2",
}

DEVICE_GROUP_CONFIG = {
    "imsis": [],
    "site-info": "demo",
    "ip-domain-name": "pool1",
    "ip-domain-expanded": {
        "dnn": "internet",
        "ue-ip-pool": "172.250.1.0/16",
        "dns-primary": "8.8.8.8",
        "mtu": 1460,
        "ue-dnn-qos": {
            "dnn-mbr-uplink": 200000000,
            "dnn-mbr-downlink": 200000000,
            "bitrate-unit": "bps",
            "traffic-class": {"name": "platinum", "arp": 6, "pdb": 300, "pelr": 6, "qci": 8},
        },
    },
}


NETWORK_SLICE_CONFIG = {
    "slice-id": {"sst": "1", "sd": "102030"},
    "site-device-group": [],
    "site-info": {
        "site-name": "demo",
        "plmn": {"mcc": "001", "mnc": "01"},
        "gNodeBs": [{"name": "ran-gnbsim-gnbsim", "tac": 1}],
        "upf": {"upf-name": "upf-external", "upf-port": "8805"},
    },
}


@dataclass
class StatusResponse:
    """Response from NMS when checking the status."""

    initialized: bool


@dataclass
class LoginParams:
    """Parameters to login to NMS."""

    username: str
    password: str


@dataclass
class LoginResponse:
    """Response from NMS when logging in."""

    token: str


class NMS:
    """Handle NMS API calls."""

    def __init__(self, url: str):
        if url.endswith("/"):
            url = url[:-1]
        self.url = url

    def _make_request(
        self,
        method: str,
        endpoint: str,
        token: Optional[str] = None,
        data: any = None,  # type: ignore[reportGeneralTypeIssues]
    ) -> Any | None:
        """Make an HTTP request and handle common error patterns."""
        headers = JSON_HEADER
        if token:
            headers["Authorization"] = f"Bearer {token}"
        url = f"{self.url}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                verify=False,
            )
        except requests.exceptions.SSLError as e:
            logger.error("SSL error: %s", e)
            return None
        except requests.RequestException as e:
            logger.error("HTTP request failed: %s", e)
            return None
        except OSError as e:
            logger.error("couldn't complete HTTP request: %s", e)
            return None
        try:
            response.raise_for_status()
        except requests.HTTPError:
            logger.error(
                "Request failed: code %s",
                response.status_code,
            )
            return None
        try:
            json_response = response.json()
        except json.JSONDecodeError:
            return None
        return json_response

    def is_initialized(self) -> bool:
        """Return if NMS is initialized."""
        status = self.get_status()
        return status.initialized if status else False

    def is_api_available(self) -> bool:
        """Return if NMS is reachable."""
        status = self.get_status()
        return status is not None

    def get_status(self) -> StatusResponse | None:
        """Return if NMS is initialized."""
        response = self._make_request("GET", "/status")
        if response:
            return StatusResponse(
                initialized=response.get("initialized"),
            )
        return None

    def wait_for_api_to_be_available(self, timeout: int = 300) -> None:
        """Wait for NMS API to be available."""
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.is_api_available():
                return
            time.sleep(5)
        raise TimeoutError(f"NMS API is not available after {timeout} seconds.")

    def wait_for_initialized(self, timeout: int = 300) -> None:
        """Wait for NMS to be initialized."""
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.is_initialized():
                return
            time.sleep(5)
        raise TimeoutError(f"NMS is not initialized after {timeout} seconds.")

    def login(self, username: str, password: str) -> LoginResponse | None:
        """Login to NMS by sending the username and password and return a Token."""
        login_params = LoginParams(username=username, password=password)
        response = self._make_request("POST", "/login", data=asdict(login_params))
        if response:
            return LoginResponse(
                token=response.get("token"),
            )
        return None

    def create_subscriber(self, imsi: str, token: str) -> None:
        """Create a subscriber."""
        url = f"/api/subscriber/imsi-{imsi}"
        data = SUBSCRIBER_CONFIG.copy()
        data["UeId"] = imsi
        self._make_request("POST", url, token=token, data=data)
        logger.info(f"Created subscriber with IMSI {imsi}.")

    def create_device_group(self, name: str, imsis: List[str], token: str) -> None:
        """Create a device group."""
        DEVICE_GROUP_CONFIG["imsis"] = imsis
        url = f"/config/v1/device-group/{name}"
        self._make_request("POST", url, token=token, data=DEVICE_GROUP_CONFIG)
        logger.info(f"Created device group {name}.")

    def create_network_slice(self, name: str, device_groups: List[str], token: str) -> None:
        """Create a network slice."""
        NETWORK_SLICE_CONFIG["site-device-group"] = device_groups
        url = f"/config/v1/network-slice/{name}"
        self._make_request("POST", url, token=token, data=NETWORK_SLICE_CONFIG)
        logger.info(f"Created network slice {name}.")
