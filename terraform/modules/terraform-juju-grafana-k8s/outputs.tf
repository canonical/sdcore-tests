# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.grafana.name
}

output "ingress_endpoint" {
  description = "Name of the endpoint used by Grafana for the ingress configuration."
  value       = "ingress"
}

output "catalogue_endpoint" {
  description = "Name of the endpoint used by Grafana for the Catalogue integration."
  value       = "catalogue"
}

output "grafana_dashboard_endpoint" {
  description = "Name of the endpoint used by Grafana for handling dashboards sent by client applications."
  value       = "grafana-dashboard"
}

output "grafana_source_endpoint" {
  description = "Name of the endpoint used by Grafana for accepting data source configurations sent by client applications."
  value       = "grafana-source"
}

output "metrics_endpoint" {
  description = "Exposes the Prometheus metrics endpoint providing telemetry about the Grafana instance."
  value       = "metrics-endpoint"
}
