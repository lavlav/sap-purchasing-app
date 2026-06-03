group "default" {
  targets = ["api", "dashboard"]
}

variable "IMAGE_BASE" {
  default = ""
}

variable "IMAGE_TAG" {
  default = "latest"
}

target api {
    context = "./Dashboard Data API"
    dockerfile = "Dockerfile"
    contexts = {
        common = "./Dashboard Common/"
    }
    tags = ["${IMAGE_BASE}data-api:${IMAGE_TAG}"]
}

target dashboard {
    context = "./Purchasing Dashboard"
    dockerfile = "Dockerfile"
    contexts = {
        common = "./Dashboard Common/"
    }
    tags = ["${IMAGE_BASE}purchasing-dashboard:${IMAGE_TAG}"]
}