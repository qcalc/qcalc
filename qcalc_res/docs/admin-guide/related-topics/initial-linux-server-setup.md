## Initial Linux Server Setup
<!-- TOC -->
  * [Initial Linux Server Setup](#initial-linux-server-setup)
    * [a. Create a non-root user](#a-create-a-non-root-user)
    * [b. Set up passwordless SSH access (from your local machine)](#b-set-up-passwordless-ssh-access-from-your-local-machine)
    * [c. Update the system](#c-update-the-system)
    * [d. Create swap space](#d-create-swap-space-)
<!-- TOC -->
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

Recommended for small servers with 4GB of RAM or less. First, check if swap is already configured by running free -h. The command below creates a 1GB swap file. However, it is generally recommended to match your swap size to your total RAM.

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---