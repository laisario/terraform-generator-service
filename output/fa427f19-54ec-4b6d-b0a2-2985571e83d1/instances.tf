resource "aws_instance" "web_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  vpc_security_group_ids = [aws_security_group.web_sg.id]
}
