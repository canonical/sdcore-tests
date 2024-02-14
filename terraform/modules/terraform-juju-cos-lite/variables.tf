# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

variable "model_name" {
  description = "Name of the Juju model to deploy applications to."
  type        = string
  default     = "cos"
}

# Alertmanager
variable "alertmanager_app_name" {
  description = "Name of the Alertmanager application."
  type        = string
  default     = "alertmanager"
}
variable "alertmanager_channel" {
  description = "The channel to use when deploying Alertmanager charm."
  type        = string
  default     = "stable"
}

# Catalogue
variable "catalogue_app_name" {
  description = "Name of the Catalogue application."
  type        = string
  default     = "catalogue"
}
variable "catalogue_channel" {
  description = "The channel to use when deploying Catalogue charm."
  type        = string
  default     = "stable"
}

# COS Configuration
variable "deploy_cos_configuration" {
  description = "Controls whether the cos-configuration-k8s charm will be deployed as part of the stack or not."
  type        = bool
  default     = false
}
variable "cos_configuration_app_name" {
  description = "Name of the cos-configuration application."
  type        = string
  default     = "cos-configuration"
}
variable "cos_configuration_channel" {
  description = "The channel to use when deploying cos-configuration-k8s charm."
  type        = string
  default     = "stable"
}
variable "git_repo" {
  description = "URL to repo to clone and sync against."
  type        = string
  default     = ""
}
variable "git_branch" {
  description = "The git branch to check out."
  type        = string
  default     = "master"
}
variable "git_rev" {
  description = "The git revision (tag or hash) to check out."
  type        = string
  default     = "HEAD"
}
variable "git_depth" {
  description = "Cloning depth, to truncate commit history to the specified number of commits. Zero means no truncating."
  type        = number
  default     = 1
}
variable "git_ssh_key" {
  description = "An optional SSH private key to use when cloning the repository."
  type        = string
  default     = ""
}
variable "prometheus_alert_rules_path" {
  description = "Relative path in repo to prometheus rules."
  type        = string
  default     = "prometheus_alert_rules"
}
variable "loki_alert_rules_path" {
  description = "Relative path in repo to loki rules."
  type        = string
  default     = "loki_alert_rules"
}
variable "grafana_dashboards_path" {
  description = "Relative path in repo to grafana dashboards."
  type        = string
  default     = "grafana_dashboards"
}

# Grafana
variable "grafana_app_name" {
  description = "Name of the Grafana application."
  type        = string
  default     = "grafana"
}
variable "grafana_channel" {
  description = "The channel to use when deploying Grafana charm."
  type        = string
  default     = "stable"
}

# Loki
variable "loki_app_name" {
  description = "Name of the Loki application."
  type        = string
  default     = "loki"
}
variable "loki_channel" {
  description = "The channel to use when deploying Loki charm."
  type        = string
  default     = "stable"
}

# Prometheus
variable "prometheus_app_name" {
  description = "Name of the Prometheus application."
  type        = string
  default     = "prometheus"
}
variable "prometheus_channel" {
  description = "The channel to use when deploying Prometheus charm."
  type        = string
  default     = "stable"
}

# Traefik
variable "traefik_app_name" {
  description = "Name of the Traefik application."
  type        = string
  default     = "traefik"
}
variable "traefik_channel" {
  description = "The channel to use when deploying Traefik charm."
  type        = string
  default     = "stable"
}
