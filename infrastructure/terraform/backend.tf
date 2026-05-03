terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "tiktok-ai-tf-state"
    key            = "prod/terraform.tfstate"
    region         = "ap-southeast-1"
    dynamodb_table = "tiktok-ai-tf-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}
