resource "aws_security_group" "web_sg" {
  name        = "web-tier-sg"
  description = "Security group for web servers"
  vpc_id      = aws_vpc.main.id
  dynamic "ingress" {
    for_each = [{"cidr_blocks": "[\"0.0.0.0/0\"]", "from_port": 80, "protocol": "tcp", "to_port": 80}, {"cidr_blocks": "[\"0.0.0.0/0\"]", "from_port": 443, "protocol": "tcp", "to_port": 443}]
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }
}
resource "aws_security_group" "app_sg" {
  name        = "app-tier-sg"
  description = "Security group for application servers"
  vpc_id      = aws_vpc.main.id
  dynamic "ingress" {
    for_each = [{"cidr_blocks": "[\"10.0.0.0/16\"]", "from_port": 8080, "protocol": "tcp", "to_port": 8080}]
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }
}
resource "aws_security_group" "worker_sg" {
  name        = "worker-tier-sg"
  description = "Security group for background workers"
  vpc_id      = aws_vpc.main.id
  dynamic "ingress" {
    for_each = [{"cidr_blocks": "[\"10.0.0.0/16\"]", "from_port": 6379, "protocol": "tcp", "to_port": 6379}]
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }
}
