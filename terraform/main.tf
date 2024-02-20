# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

resource "juju_model" "sdcore" {
  name = var.sdcore_model_name
}

module "cos-lite" {
  source = "./modules/terraform-juju-cos-lite"

  model_name = var.cos_model_name
  deploy_cos_configuration = true
  git_repo                 = "https://github.com/canonical/sdcore-cos-configuration"
  git_branch               = "main"
  grafana_dashboards_path  = "grafana_dashboards/sdcore/"
}

module "sdcore-router" {
  source = "git::https://github.com/canonical/sdcore-router-k8s-operator//terraform"

  model_name = juju_model.sdcore.name
  depends_on = [juju_model.sdcore]
}

module "sdcore" {
  source = "git::https://github.com/canonical/terraform-juju-sdcore-k8s//modules/sdcore-k8s"

  model_name = juju_model.sdcore.name
  create_model = false

  depends_on = [module.sdcore-router]
}

module "gnbsim" {
  source = "git::https://github.com/canonical/sdcore-gnbsim-k8s-operator//terraform"

  model_name = juju_model.sdcore.name
  depends_on = [module.sdcore-router]
}

resource "juju_integration" "gnbsim-amf" {
  model = juju_model.sdcore.name

  application {
    name     = module.gnbsim.app_name
    endpoint = module.gnbsim.fiveg_n2_endpoint
  }

  application {
    name     = module.sdcore.amf_app_name
    endpoint = module.sdcore.fiveg_n2_endpoint
  }
}

resource "juju_integration" "gnbsim-nms" {
  model = juju_model.sdcore.name

  application {
    name     = module.gnbsim.app_name
    endpoint = module.gnbsim.fiveg_gnb_identity_endpoint
  }

  application {
    name     = module.sdcore.nms_app_name
    endpoint = module.sdcore.fiveg_gnb_identity_endpoint
  }
}

# Cross-model integrations

resource "juju_offer" "prometheus-remote-write" {
  model            = module.cos-lite.model_name
  application_name = module.cos-lite.prometheus_app_name
  endpoint         = "receive-remote-write"
}
resource "juju_offer" "loki-logging" {
  model            = module.cos-lite.model_name
  application_name = module.cos-lite.loki_app_name
  endpoint         = "logging"
}

resource "juju_integration" "prometheus" {
  model = juju_model.sdcore.name

  application {
    name     = module.sdcore.grafana_agent_app_name
    endpoint = module.sdcore.send_remote_write_endpoint
  }

  application {
    offer_url = juju_offer.prometheus-remote-write.url
  }
}

resource "juju_integration" "loki" {
  model = juju_model.sdcore.name

  application {
    name     = module.sdcore.grafana_agent_app_name
    endpoint = module.sdcore.logging_consumer_endpoint
  }

  application {
    offer_url = juju_offer.loki-logging.url
  }
}
