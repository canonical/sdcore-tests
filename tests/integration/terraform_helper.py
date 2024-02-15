#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import os
from enum import Enum
from shutil import which
from subprocess import CalledProcessError, check_call
from typing import Optional

logger = logging.getLogger(__name__)

TERRAFORM_APP_NAME = "terraform"


class TerraformCommands(str, Enum):
    init = "init"
    plan = "plan"
    apply = "apply"


class TerraformError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class Terraform:
    def __init__(self, work_dir: Optional[str] = os.getcwd()):
        if not self._terraform_available():
            raise TerraformError("Terraform executable not found. Please install Terraform!")
        if not os.path.exists(work_dir):
            raise TerraformError("Given `work_dir` does not exist!")
        self.work_dir = work_dir

    def init(self):
        logger.info(f"Running `{TERRAFORM_APP_NAME} {TerraformCommands.init}` in {self.work_dir}")
        try:
            self._run_terraform_cmd(TerraformCommands.init)
        except CalledProcessError as e:
            raise TerraformError(
                f"Error running `{TERRAFORM_APP_NAME} {TerraformCommands.init}`"
            ) from e

    def plan(self):
        logger.info(f"Running `{TERRAFORM_APP_NAME} {TerraformCommands.plan}` in {self.work_dir}")
        try:
            self._run_terraform_cmd(TerraformCommands.plan)
        except CalledProcessError as e:
            raise TerraformError(
                f"Error running `{TERRAFORM_APP_NAME} {TerraformCommands.plan}`"
            ) from e

    def apply(self, auto_approve: Optional[bool] = True):
        logger.info(f"Running `{TERRAFORM_APP_NAME} {TerraformCommands.apply}` in {self.work_dir}")
        args = []
        if auto_approve:
            args.append("-auto-approve")
        try:
            self._run_terraform_cmd(TerraformCommands.apply, *args)
        except CalledProcessError as e:
            raise TerraformError(
                f"Error running `{TERRAFORM_APP_NAME} {TerraformCommands.apply}`"
            ) from e

    @staticmethod
    def _terraform_available() -> bool:
        return which(TERRAFORM_APP_NAME) is not None

    def _run_terraform_cmd(self, terraform_command: str, *args) -> int:
        return check_call([TERRAFORM_APP_NAME, terraform_command, *args], cwd=self.work_dir)
