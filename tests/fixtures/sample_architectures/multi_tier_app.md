# Multi-Tier E-Commerce Architecture

A production-ready architecture with multiple S3 buckets, EC2 instances across tiers,
VPC networking, and security groups.

## Networking

```terraform
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name        = "ecommerce-vpc"
    Environment = "production"
  }
}

resource "aws_subnet" "public_1a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  tags = {
    Name = "public-1a"
  }
}

resource "aws_subnet" "public_1b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
  tags = {
    Name = "public-1b"
  }
}

resource "aws_subnet" "private_1a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "us-east-1a"
  tags = {
    Name = "private-1a"
  }
}
```

## Security Groups

```terraform
resource "aws_security_group" "web_sg" {
  name        = "web-tier-sg"
  description = "Security group for web servers"
  vpc_id      = aws_vpc.main.id
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = {
    Tier = "web"
  }
}

resource "aws_security_group" "app_sg" {
  name        = "app-tier-sg"
  description = "Security group for application servers"
  vpc_id      = aws_vpc.main.id
  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
  tags = {
    Tier = "app"
  }
}

resource "aws_security_group" "worker_sg" {
  name        = "worker-tier-sg"
  description = "Security group for background workers"
  vpc_id      = aws_vpc.main.id
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
  tags = {
    Tier = "worker"
  }
}
```

## S3 Buckets

```terraform
resource "aws_s3_bucket" "assets_bucket" {
  bucket = "ecommerce-assets-prod"
  tags = {
    Purpose     = "static-assets"
    Environment = "production"
  }
}

resource "aws_s3_bucket" "logs_bucket" {
  bucket = "ecommerce-logs-prod"
  tags = {
    Purpose     = "access-logs"
    Environment = "production"
  }
}

resource "aws_s3_bucket" "backups_bucket" {
  bucket = "ecommerce-backups-prod"
  tags = {
    Purpose     = "database-backups"
    Environment = "production"
  }
}
```

## Compute - Web Tier

```terraform
resource "aws_instance" "web_1" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type           = "t3.small"
  vpc_security_group_ids  = [aws_security_group.web_sg.id]
  tags = {
    Role = "web"
    Name = "web-1"
  }
}

resource "aws_instance" "web_2" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type           = "t3.small"
  vpc_security_group_ids  = [aws_security_group.web_sg.id]
  tags = {
    Role = "web"
    Name = "web-2"
  }
}
```

## Compute - Application Tier

```terraform
resource "aws_instance" "app_1" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type           = "t3.medium"
  vpc_security_group_ids  = [aws_security_group.app_sg.id]
  tags = {
    Role = "app"
    Name = "app-1"
  }
}

resource "aws_instance" "app_2" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type           = "t3.medium"
  vpc_security_group_ids  = [aws_security_group.app_sg.id]
  tags = {
    Role = "app"
    Name = "app-2"
  }
}
```

## Compute - Worker Tier

```terraform
resource "aws_instance" "worker_1" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type           = "t3.micro"
  vpc_security_group_ids  = [aws_security_group.worker_sg.id]
  tags = {
    Role = "worker"
    Name = "worker-1"
  }
}
```
