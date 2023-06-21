#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import logging

import requests

logger = logging.getLogger(__name__)

SUBSCRIBER_JSON = {
    "UeId": "PLACEHOLDER",
    "plmnId": "20801",
    "opc": "981d464c7c52eb6e5036234984ad0bcf",
    "key": "5122250214c33e723a5dd523fc145fc0",
    "sequenceNumber": "16f3b3f70fc2",
}
DEVICE_GROUP_JSON = {
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
            "traffic-class": {"name": "platinum", "arp": 6, "pdb": 300, "pelr": 6, "qci": 8},
        },
    },
}
NETWORK_SLICE_JSON = {
    "slice-id": {"sst": "1", "sd": "010203"},
    "site-device-group": [],
    "site-info": {
        "site-name": "demo",
        "plmn": {"mcc": "208", "mnc": "93"},
        "gNodeBs": [{"name": "demo-gnb1", "tac": 1}],
        "upf": {"upf-name": "upf", "upf-port": "8805"},
    },
}


class WebUI:
    def __init__(self, webui_ip: str) -> None:
        """Constructor.

        Args:
            webui_ip (str): IP address of the WebUI application unit
        """
        self.webui_ip = webui_ip

    def create_subscriber(self, imsi: str) -> None:
        """Creates a subscriber.

        Args:
            imsi (str): Subscriber's IMSI
        """
        SUBSCRIBER_JSON["UeId"] = imsi
        url = f"http://{self.webui_ip}:5000/api/subscriber/imsi-{imsi}"
        response = requests.post(url=url, data=json.dumps(SUBSCRIBER_JSON))
        response.raise_for_status()

    def create_device_group(self, device_group_name: str, imsis: list) -> None:
        """Creates a device group.

        Args:
            device_group_name (str): Device group name
            imsis (list): List of IMSIS to be included in the device group
        """
        DEVICE_GROUP_JSON["imsis"] = imsis
        url = f"http://{self.webui_ip}:5000/config/v1/device-group/{device_group_name}"
        response = requests.post(url, json=DEVICE_GROUP_JSON)
        response.raise_for_status()

    def create_network_slice(self, network_slice_name: str, device_groups: list) -> None:
        """Creates a network slice.

        Args:
            network_slice_name (str): Network slice name
            device_groups (list): List of device groups to be included in the network slice
        """
        NETWORK_SLICE_JSON["site-device-group"] = device_groups
        url = f"http://{self.webui_ip}:5000/config/v1/network-slice/{network_slice_name}"
        response = requests.post(url, json=NETWORK_SLICE_JSON)
        response.raise_for_status()