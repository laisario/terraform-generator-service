resource "aws_security_group" "web_sg" {
  name        = "web-sg"
  description = "Security group for web servers"
  dynamic "ingress" {
    for_each = [{"cidr_blocks": "[\"0.0.0.0/0\"]", "from_port": 80, "protocol": "tcp", "to_port": 80}]
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }
}
