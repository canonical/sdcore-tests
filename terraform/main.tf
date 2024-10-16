# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

resource "juju_model" "sdcore" {
  name = var.sdcore_model_name
}

module "sdcore-router" {
  source = "git::https://github.com/canonical/sdcore-router-k8s-operator//terraform"

  model      = juju_model.sdcore.name
  depends_on = [juju_model.sdcore]
}

module "sdcore" {
  source = "git::https://github.com/canonical/terraform-juju-sdcore-k8s//modules/sdcore-k8s"

  model = juju_model.sdcore.name

  depends_on = [module.sdcore-router]
}

resource "juju_model" "ran-simulator" {
  name = "ran"
}

module "gnbsim" {
  source = "git::https://github.com/canonical/sdcore-gnbsim-k8s-operator//terraform"

  model      = juju_model.ran-simulator.name
  depends_on = [module.sdcore-router]
}

resource "juju_offer" "gnbsim-fiveg-gnb-identity" {
  model            = juju_model.ran-simulator.name
  application_name = module.gnbsim.app_name
  endpoint         = module.gnbsim.provides.fiveg_gnb_identity
}

resource "juju_integration" "gnbsim-amf" {
  model = juju_model.ran-simulator.name

  application {
    name     = module.gnbsim.app_name
    endpoint = module.gnbsim.requires.fiveg_n2
  }

  application {
    offer_url = module.sdcore.amf_fiveg_n2_offer_url
  }
}

resource "juju_integration" "gnbsim-nms" {
  model = juju_model.sdcore.name

  application {
    name     = module.sdcore.nms_app_name
    endpoint = module.sdcore.fiveg_gnb_identity_endpoint
  }

  application {
    offer_url = juju_offer.gnbsim-fiveg-gnb-identity.url
  }
}

module "cos" {
  source                   = "git::https://github.com/canonical/terraform-juju-sdcore//modules/external/cos-lite"
  model_name               = "cos-lite"
  deploy_cos_configuration = true
  cos_configuration_config = {
    git_repo                = "https://github.com/canonical/sdcore-cos-configuration"
    git_branch              = "main"
    grafana_dashboards_path = "grafana_dashboards/sdcore/"
  }
}

resource "juju_integration" "prometheus-remote-write" {
  model = juju_model.sdcore.name

  application {
    name     = module.sdcore.grafana_agent_app_name
    endpoint = module.sdcore.send_remote_write_endpoint
  }

  application {
    offer_url = module.cos.prometheus_remote_write_offer_url
  }
}

resource "juju_integration" "loki-logging" {
  model = juju_model.sdcore.name

  application {
    name     = module.sdcore.grafana_agent_app_name
    endpoint = module.sdcore.logging_consumer_endpoint
  }

  application {
    offer_url = module.cos.loki_logging_offer_url
  }
}
