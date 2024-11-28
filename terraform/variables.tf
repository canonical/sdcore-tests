# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

variable "sdcore_model_name" {
  description = "Name of Juju model to deploy SD-Core applications to."
  type        = string
  default     = "sdcore"
}

variable "ran_model_name" {
  description = "Name of Juju model to deploy RAN simulator to."
  type        = string
  default     = "ran"
}
