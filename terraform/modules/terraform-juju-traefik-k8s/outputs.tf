# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.traefik.name
}

output "ingress_endpoint" {
  description = "Provides ingress-like routing to the related Juju application, load-balancing across all units."
  value       = "ingress"
}

output "ingress_per_unit_endpoint" {
  description = "Provides ingress-like routing to the single units of the related Juju application."
  value       = "ingress-per-unit"
}

output "traefik_route_endpoint" {
  description = "Provides endpoint for a traefik-route charm to sit between Traefik and a charm in need of ingress, configuring the relation on a per-unit basis."
  value       = "traefik-route"
}

output "metrics_endpoint" {
  description = "Exposes the Prometheus metrics endpoint providing telemetry about the Traefik instance."
  value       = "metrics-endpoint"
}

output "grafana_dashboard_endpoint" {
  description = "Forwards the built-in grafana dashboard(s) for monitoring Traefik."
  value       = "grafana-dashboard"
}
