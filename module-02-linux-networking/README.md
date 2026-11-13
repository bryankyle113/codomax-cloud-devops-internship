# Module 02: Linux, Networking & Cloud Infrastructure

**Internship Track:** Cloud Computing & DevOps Internship — Codomax Digital Solutions  
**Intern:** Bryan Kyle Dimpal  

## Overview
This module documents the provisioning, hardening, and deployment of an Ubuntu Server 24.04.5 LTS virtual machine (`codomax-server`) running an Nginx web server, administered remotely via Ed25519 SSH key-based authentication.

## Architecture & Network Configuration
- **Operating System:** Ubuntu Server 24.04.5 LTS (`codomax-server`)
- **Network Mode:** NAT Virtual Network (`ens33` interface assigned `192.168.146.129`)
- **Remote Administration:** Ed25519 SSH cryptographic key-pair authentication (`ssh-keygen` + `ssh-copy-id`)
- **Firewall Rules (UFW):**
  - `22/tcp` (SSH) — `ALLOW` (Secure remote terminal access)
  - `80/tcp` (HTTP) — `ALLOW` (Public web traffic to Nginx)

## Key Implementation Steps
1. **Provisioned Virtual Server:** Installed Ubuntu Server 24.04.5 LTS with OpenSSH enabled and verified IP routing (`ip a`).
2. **Secured Remote Access:** Generated an Ed25519 SSH key pair on the client workstation and deployed the public key to `~/.ssh/authorized_keys` on the server for passwordless login.
3. **Linux Administration & Access Control:** Created a dedicated `devops_team` group and `devops_intern` user, and restricted `/opt/codomax_app` using `chown` and `chmod 750`.
4. **Firewall & Port Security:** Configured Uncomplicated Firewall (UFW) to explicitly permit Ports `22` and `80` before enabling active filtering.
5. **Service Deployment & Verification:** Installed Nginx, enabled it via `systemd` (`systemctl enable nginx`), published a custom landing page, and verified HTTP connectivity from a client browser (`http://192.168.146.129`).

## Verification Screenshots
All deployment and verification screenshots are located in the [`screenshots/`](./screenshots) directory.
