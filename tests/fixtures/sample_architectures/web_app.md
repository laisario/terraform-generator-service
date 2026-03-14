# Web Application Architecture

## S3 Buckets

We need an S3 bucket for static assets.

```terraform
resource "aws_s3_bucket" "assets_bucket" {
  bucket = "my-app-assets"
  tags = {
    Environment = "production"
    Project     = "web-app"
  }
}
```

## Security Groups

```terraform
resource "aws_security_group" "web_sg" {
  name        = "web-sg"
  description = "Security group for web servers"
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

## Compute

```terraform
resource "aws_instance" "web_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  tags = {
    Role = "web"
  }
}
```
