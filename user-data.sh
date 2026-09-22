#!/bin/bash
apt-get update -y
apt-get install -y docker.io awscli
systemctl enable --now docker
usermod -aG docker ubuntu