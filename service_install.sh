sudo echo "
[Unit]
Description=OltreBot service
After=network.target
[Service]
Type=simple
User=mark
Restart=always
EnvironmentFile=/mark/HorusElohim/OltreBot/.env
ExecStart=/mark/HorusElohim/OltreBot/start.sh
[Install]
WantedBy=default.target
" > /etc/systemd/system/oltrebot.service

sudo systemctl enable oltrebot.service

sudo systemctl daemon-reload

sudo systemctl restart oltrebot.service

sudo echo "
[Unit]
Description=Lavalink service
After=network.target
[Service]
Type=simple
User=mark
Restart=always
EnvironmentFile=/mark/HorusElohim/OltreBot/.env
ExecStart=/mark/HorusElohim/OltreBot/start_lavalink.sh
[Install]
WantedBy=default.target
" > /etc/systemd/system/lavalink.service

sudo systemctl enable lavalink.service

sudo systemctl daemon-reload

sudo systemctl restart lavalink.service