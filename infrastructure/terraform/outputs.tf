output "ec2_public_ip" {
  description = "Public IP of the EC2 instance (use for SSH and Cloudflare tunnel config)"
  value       = aws_instance.app.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS of the EC2 instance"
  value       = aws_instance.app.public_dns
}

output "ecr_backend_url" {
  description = "ECR URL for the backend image — set as ECR_REGISTRY/ECR_BACKEND_REPO in GitHub vars"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_url" {
  description = "ECR URL for the frontend image — set as ECR_REGISTRY/ECR_FRONTEND_REPO in GitHub vars"
  value       = aws_ecr_repository.frontend.repository_url
}

output "ecr_registry" {
  description = "ECR registry hostname (account_id.dkr.ecr.region.amazonaws.com) — set as ECR_REGISTRY in GitHub vars"
  value       = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com"
}

output "google_creds_secret_arn" {
  description = "ARN of the Secrets Manager secret for google-creds.json — paste your JSON as the secret value"
  value       = aws_secretsmanager_secret.google_creds.arn
}

data "aws_caller_identity" "current" {}
