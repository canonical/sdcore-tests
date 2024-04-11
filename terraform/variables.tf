# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

variable "sdcore_model_name" {
  description = "Name of Juju model to deploy application to."
  type        = string
  default     = "sdcore"
}

variable "amf_channel" {
  description = "The channel to use when deploying `sdcore-amf-k8s` charm."
  type        = string
  default     = "1.4/edge"
}

variable "ausf_channel" {
  description = "The channel to use when deploying `sdcore-ausf-k8s` charm."
  type        = string
  default     = "1.4/edge"
}

variable "nms_channel" {
  description = "The channel to use when deploying `sdcore-nms-k8s` charm."
  type        = string
  default     = "0.2/edge"
}

variable "nrf_channel" {
  description = "The channel to use when deploying `sdcore-nrf-k8s` charm."
  type        = string
  default     = "1.4/edge"
}

variable "nssf_channel" {
  description = "The channel to use when deploying `sdcore-nssf-k8s` charm."
  type        = string
  default     = "1.4/edge"
}

variable "pcf_channel" {
  description = "The channel to use when deploying `sdcore-pcf-k8s` charm."
  type        = string
  default     = "1.4/edge"
}

variable "smf_channel" {
  description = "The channel to use when deploying `sdcore-smf-k8s` charm."
  type        = string
  default     = "1.4/edge"
}

variable "udm_channel" {
  description = "The channel to use when deploying `sdcore-udm-k8s` charm."
  type        = string
  default     = "1.4/edge"
}

variable "udr_channel" {
  description = "The channel to use when deploying `sdcore-udr-k8s` charm."
  type        = string
  default     = "1.4/edge"
}

variable "upf_channel" {
  description = "The channel to use when deploying `sdcore-upf-k8s` charm."
  type        = string
  default     = "1.4/edge"
}

variable "webui_channel" {
  description = "The channel to use when deploying `sdcore-webui-k8s` charm."
  type        = string
  default     = "1.4/edge"
}
