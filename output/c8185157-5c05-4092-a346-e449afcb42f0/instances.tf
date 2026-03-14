resource "aws_instance" "web_1" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.small"
  vpc_security_group_ids = [aws_security_group.web_sg.id]
}
resource "aws_instance" "web_2" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.small"
  vpc_security_group_ids = [aws_security_group.web_sg.id]
}
resource "aws_instance" "app_1" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
  vpc_security_group_ids = [aws_security_group.app_sg.id]
}
resource "aws_instance" "app_2" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
  vpc_security_group_ids = [aws_security_group.app_sg.id]
}
resource "aws_instance" "worker_1" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  vpc_security_group_ids = [aws_security_group.worker_sg.id]
}
