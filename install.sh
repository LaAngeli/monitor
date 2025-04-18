#!/bin/bash

# Actualizare sistem
apt update
apt upgrade -y

# Instalare dependențe
apt install -y python3 python3-pip python3-venv mysql-server nginx git

# Configurare MySQL
mysql_secure_installation

# Creare director pentru aplicație
mkdir -p /var/www/youtube-monitor
chown -R $USER:$USER /var/www/youtube-monitor

# Clonează codul aplicației
cd /var/www/youtube-monitor
git clone URL_REPO_TAU .

# Creare și activare virtual environment
python3 -m venv venv
source venv/bin/activate

# Instalare dependențe Python
pip install -r requirements.txt

# Configurare serviciu systemd
cp youtube-monitor.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable youtube-monitor
systemctl start youtube-monitor

# Configurare Nginx
cp nginx.conf /etc/nginx/sites-available/youtube-monitor
ln -s /etc/nginx/sites-available/youtube-monitor /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# Configurare firewall
ufw allow 'Nginx Full'
ufw allow 'OpenSSH'
ufw enable

echo "Instalarea a fost finalizată cu succes!"
echo "Verifică statusul serviciului cu: systemctl status youtube-monitor"
echo "Verifică log-urile cu: journalctl -u youtube-monitor" 