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
    apply = "apply"


class TerraformError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class TerraformClient:
    def __init__(self, work_dir: str = os.getcwd()):
        """Construct the TerraformClient.

        Args:
            work_dir(str): Directory containing Terraform root module. Defaults to current working
                directory.
        """
        if not self._terraform_available():
            raise TerraformError("Terraform executable not found. Please install Terraform!")
        if not os.path.exists(work_dir):
            raise TerraformError("Given `work_dir` does not exist!")
        self.work_dir = work_dir

    def init(self):
        """Initialize the Terraform provider.

        Equivalent to `terraform init` CLI command.

        Raises:
            TerraformError: Custom error raised when initialization of the provider fails
        """
        logger.info(f"Running `{TERRAFORM_APP_NAME} {TerraformCommands.init}` in {self.work_dir}")
        try:
            self._run_terraform_cmd(TerraformCommands.init)
        except CalledProcessError as e:
            raise TerraformError(
                f"Error running `{TERRAFORM_APP_NAME} {TerraformCommands.init}`"
            ) from e

    def apply(self, auto_approve: Optional[bool] = True):
        """Apply the Terraform plan based on the module.

        Equivalent to `terraform apply` CLI command.

        Args:
            auto_approve (bool): Skips the confirmation before applying the plan

        Raises:
            TerraformError: Custom error raised when initialization of the provider fails
        """
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
        """Check whether the Terraform executable is installed.

        Returns:
            bool: Whether the Terraform executable is installed
        """
        return which(TERRAFORM_APP_NAME) is not None

    def _run_terraform_cmd(self, terraform_command: str, *args) -> int:
        """Run Terraform command.

        Args:
            terraform_command(str): Terraform command to execute
            args: List of arguments for the Terraform command

        Returns:
            int: Command's return code
        """
        logger.info(f'Running: {" ".join([TERRAFORM_APP_NAME, terraform_command, *args])}')
        return check_call([TERRAFORM_APP_NAME, terraform_command, *args], cwd=self.work_dir)
