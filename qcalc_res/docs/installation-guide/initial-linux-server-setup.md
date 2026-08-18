## Initial Linux Server Setup

Following instructions have used placeholders shown below. Replace these placeholders with appropriate values before executing the instructions.

- `<yourdomain.com>`
- `<user_name>`
- `<your_email_id>`

### a. Create a non-root user

```bash
ssh root@<yourdomain.com>
adduser <user_name>
usermod -aG sudo <user_name>
exit
```

### b. Set up passwordless SSH access (from your local machine)

```bash
# On your local machine
cd ~/.ssh
ssh-keygen           # skip if a key already exists
scp id_rsa.pub <your_email_id>:~/.ssh/authorized_keys
```

Log in as the new user for all remaining steps:

```bash
ssh <user_name>@<yourdomain.com>
```

### c. Update the system

```bash
sudo apt update && sudo apt upgrade -y
```

### d. Create swap space 

This step is optional. It is recommended for small VPS having 2GB RAM or less.

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---