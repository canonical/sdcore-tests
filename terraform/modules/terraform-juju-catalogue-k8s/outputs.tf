# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "Name of the deployed application."
  value       = juju_application.catalogue.name
}

output "ingress_endpoint" {
  description = "Name of the endpoint used by the Catalogue for the ingress configuration."
  value       = "ingress"
}

output "catalogue_endpoint" {
  description = "Name of the endpoint used by the Catalogue for integrating with other applications."
  value       = "catalogue"
}

