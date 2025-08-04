#!/bin/bash

set -e

# Ensure we run as root
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root. Use: sudo ./setup_pi.sh"
  exit 1
fi

USERNAME="caleb"
PASSWORD="raspberry"

echo "Creating user: $USERNAME (if not exists)..."
if ! id "$USERNAME" &>/dev/null; then
  useradd -m -s /bin/bash "$USERNAME"
  echo "$USERNAME:$PASSWORD" | chpasswd
  usermod -aG sudo "$USERNAME"
fi

echo "Enabling passwordless sudo for $USERNAME..."
echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/010_$USERNAME-nopasswd

echo "Setting up auto-login on tty1..."
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat >/etc/systemd/system/getty@tty1.service.d/override.conf <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USERNAME --noclear %I \$TERM
EOF

echo "Updating packages..."
apt update

echo "Installing X server, matchbox window manager, and xterm..."
apt install -y --no-install-recommends \
  xserver-xorg xinit x11-xserver-utils \
  matchbox-window-manager xterm

echo "Installing git..."
apt install -y git

echo "Cloning and installing MHS35-show..."
runuser -l $USERNAME -c 'git clone https://github.com/goodtft/LCD-show.git'
cd /home/$USERNAME/LCD-show
chmod +x MHS35-show

# Automatically launch X on tty1 login
echo "Configuring startx to run on login..."
BASH_PROFILE="/home/$USERNAME/.bash_profile"
touch "$BASH_PROFILE"
grep -q "startx" "$BASH_PROFILE" || cat >>"$BASH_PROFILE" <<'EOF'

# Start X only on tty1
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  startx
fi
EOF

chown $USERNAME:$USERNAME "$BASH_PROFILE"

# Set up a basic .xinitrc for matchbox and xterm
echo "Creating .xinitrc file..."
cat >/home/$USERNAME/.xinitrc <<EOF
#!/bin/sh
xset s off
xset -dpms
xset s noblank
matchbox-window-manager &
xterm
EOF

chown $USERNAME:$USERNAME /home/$USERNAME/.xinitrc
chmod +x /home/$USERNAME/.xinitrc

echo "Running MHS35-show setup script (will reboot)..."
/home/$USERNAME/LCD-show/MHS35-show
