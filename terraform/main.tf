# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

resource "juju_model" "sdcore" {
  name = var.sdcore_model_name
}

module "sdcore-router" {
  source = "git::https://github.com/canonical/sdcore-router-k8s-operator//terraform?ref=v1.4"

  model_name = juju_model.sdcore.name
  depends_on = [juju_model.sdcore]
}

module "sdcore" {
  source = "git::https://github.com/canonical/terraform-juju-sdcore-k8s//modules/sdcore-k8s?ref=v1.4"

  model_name = juju_model.sdcore.name
  sdcore_channel = "1.4/edge"
  create_model = false
  deploy_cos = true

  depends_on = [module.sdcore-router]
}

module "gnbsim" {
  source = "git::https://github.com/canonical/sdcore-gnbsim-k8s-operator//terraform?ref=v1.4"

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
