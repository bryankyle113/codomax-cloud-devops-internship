#!/bin/bash
# Codomax Cloud & DevOps Internship - Module 02 Automated Server Setup
# OS: Ubuntu Server 24.04.5 LTS

set -e

echo "=== 1. Updating System Packages ==="
sudo apt update && sudo apt upgrade -y

echo "=== 2. Configuring Linux Users, Groups & Permissions ==="
sudo groupadd -f devops_team
id -u devops_intern &>/dev/null || sudo useradd -m -g devops_team -s /bin/bash devops_intern
sudo mkdir -p /opt/codomax_app
sudo chown -R devops_intern:devops_team /opt/codomax_app
sudo chmod 750 /opt/codomax_app

echo "=== 3. Configuring UFW Firewall (SSH & HTTP) ==="
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw --force enable
sudo ufw status

echo "=== 4. Installing & Configuring Nginx Web Server ==="
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx

echo '<h1>Codomax Cloud & DevOps Internship - Module 02 Live on 192.168.146.129!</h1>' | sudo tee /var/www/html/index.html

echo "=== Deployment Complete! ==="
