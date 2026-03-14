resource "aws_s3_bucket" "assets_bucket" {
  bucket = "ecommerce-assets-prod"
}
resource "aws_s3_bucket" "logs_bucket" {
  bucket = "ecommerce-logs-prod"
}
resource "aws_s3_bucket" "backups_bucket" {
  bucket = "ecommerce-backups-prod"
}
