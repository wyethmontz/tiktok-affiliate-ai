variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-southeast-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "prod"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "ssh_key_name" {
  description = "Name of the EC2 key pair for SSH access"
  type        = string
}

variable "ssh_allowed_cidr" {
  description = "CIDR block allowed to SSH into the EC2 instance (your IP)"
  type        = string
}

variable "ubuntu_ami" {
  description = "Ubuntu 22.04 LTS AMI ID for ap-southeast-1"
  type        = string
  default     = "ami-0df7a207adb9748c7"
}
