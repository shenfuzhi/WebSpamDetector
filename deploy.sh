#!/bin/bash

terraform init
terraform apply -auto-approve
# ALB_DNS_NAME=$(terraform output -raw alb_dns_name)
# echo "http://${ALB_DNS_NAME}/" > api.txt