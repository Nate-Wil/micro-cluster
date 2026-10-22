# Micro-Cluster

A self-hosted Kubernetes homelab built with **K3s, Flux CD, and GitOps**. This repository contains the declarative configurations used to deploy, manage, and maintain applications across my home Kubernetes cluster.

The goal of this project is to build practical experience with Kubernetes, infrastructure automation, GitOps workflows, and modern DevOps tooling while running useful self-hosted services.

## 🏗️ Architecture

- **K3s** — Lightweight Kubernetes distribution running across physical nodes, with a virtualized control plane.
- **Flux CD** — GitOps-based continuous delivery that reconciles cluster state with the configurations stored in Git.
- **Kustomize** — Organizes and composes Kubernetes manifests using reusable base configurations and environment-specific overlays.
- **SOPS + age** — Encrypts sensitive configuration data for secure GitOps workflows.
- **Local Path Provisioner** — Provides persistent local storage for stateful applications.
- **Traefik** — Handles cluster ingress and application routing.

## 📦 Repository Structure

```text
micro-cluster/
├── apps/
│   ├── base/          # Reusable application manifests
│   └── staging/       # Environment-specific configurations
└── clusters/
    └── staging/       # Flux cluster configuration
```

*Directory names and contents may evolve as the cluster grows.*

## 🚀 Applications

The cluster hosts a collection of self-hosted applications and supporting services, including:

- **Linkding** — Bookmark management
- **Jellyfin** — Media streaming
- **Mealie** — Recipe management
- **Habitica** — Self-hosted task and habit tracking

Additional applications and infrastructure components are managed through declarative Kubernetes manifests.

## 🔄 GitOps Workflow

Git is the source of truth for the cluster.

1. Define or update application manifests locally.
2. Commit and push changes to GitHub.
3. Flux detects repository changes and reconciles the desired state.
4. Kubernetes deploys or updates the application.
5. Application health and reconciliation status are verified using Kubernetes and Flux tooling.

This workflow allows me to manage deployments remotely without needing direct access to the cluster for every application change.

## 🔐 Security and Configuration

- Sensitive configuration is intended to be encrypted with SOPS and age before being committed to Git.
- Application configuration is separated from reusable base manifests.
- Persistent volumes are used for stateful workloads.
- Secrets, credentials, and other private configuration should never be committed to the repository in plaintext.

## 🎯 Project Goals

This is an ongoing homelab and learning project focused on:

- Kubernetes administration and troubleshooting
- GitOps and continuous delivery with Flux CD
- Declarative infrastructure and configuration management
- Secure secrets management
- Persistent storage and stateful workloads
- Infrastructure automation with Ansible and Terraform
- Building practical skills for DevOps, cloud, and platform engineering roles

## 🛠️ Philosophy

**Infrastructure as code, Git as the source of truth, and automation wherever practical.**

This project is both a functional home infrastructure platform and a hands-on environment for learning, experimenting, breaking things, and improving how I build and operate systems.
