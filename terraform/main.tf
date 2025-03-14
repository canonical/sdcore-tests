# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

data "juju_model" "sdcore" {
  name = var.sdcore_model_name
}

module "sdcore-router" {
  source = "git::https://github.com/canonical/sdcore-router-k8s-operator//terraform"

  model      = data.juju_model.sdcore.name
  depends_on = [data.juju_model.sdcore]
}

module "sdcore" {
  source = "git::https://github.com/canonical/terraform-juju-sdcore-k8s//modules/sdcore-k8s"

  model = data.juju_model.sdcore.name

  amf_config = {
    log-level = "debug"
  }
  ausf_config = {
    log-level = "debug"
  }
  nms_config = {
    log-level = "debug"
  }
  nrf_config = {
    log-level = "debug"
  }
  nssf_config = {
    log-level = "debug"
  }
  pcf_config = {
    log-level = "debug"
  }
  smf_config = {
    log-level = "debug"
  }
  udm_config = {
    log-level = "debug"
  }
  udr_config = {
    log-level = "debug"
  }
  upf_config = {
    log-level = "debug"
  }

  depends_on = [module.sdcore-router]
}

data "juju_model" "ran-simulator" {
  name = var.ran_model_name
}

module "gnbsim" {
  source = "git::https://github.com/canonical/sdcore-gnbsim-k8s-operator//terraform"

  model      = data.juju_model.ran-simulator.name

  depends_on = [module.sdcore-router]
}

resource "juju_integration" "gnbsim-amf" {
  model = data.juju_model.ran-simulator.name

  application {
    name     = module.gnbsim.app_name
    endpoint = module.gnbsim.requires.fiveg_n2
  }

  application {
    offer_url = module.sdcore.amf_fiveg_n2_offer_url
  }
}

resource "juju_integration" "gnbsim-nms" {
  model = data.juju_model.ran-simulator.name

  application {
    name     = module.gnbsim.app_name
    endpoint = module.gnbsim.requires.fiveg_core_gnb
  }

  application {
    offer_url = module.sdcore.nms_fiveg_core_gnb_offer_url
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
  model = data.juju_model.sdcore.name

  application {
    name     = module.sdcore.grafana_agent_app_name
    endpoint = module.sdcore.send_remote_write_endpoint
  }

  application {
    offer_url = module.cos.prometheus_remote_write_offer_url
  }
}

resource "juju_integration" "loki-logging" {
  model = data.juju_model.sdcore.name

  application {
    name     = module.sdcore.grafana_agent_app_name
    endpoint = module.sdcore.logging_consumer_endpoint
  }

  application {
    offer_url = module.cos.loki_logging_offer_url
  }
}
