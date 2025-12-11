provider "google" {
  project     = var.project
  region      = var.region
  zone        = var.zone
  credentials = file("../gcp-key.json")
}

# 1. Génération d'une clé SSH unique
resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "local_sensitive_file" "private_key" {
  content         = tls_private_key.ssh_key.private_key_pem
  filename        = "${path.module}/../config/id_rsa_gcp"
  file_permission = "0600"
}

# 2. Réseau & NAT
resource "google_compute_network" "vpc" {
  name                    = "k8s-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "k8s-subnet"
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.240.0.0/24"
  region        = var.region
}

resource "google_compute_router" "router" {
  name    = "k8s-router"
  network = google_compute_network.vpc.name
  region  = var.region
}

resource "google_compute_router_nat" "nat" {
  name                               = "k8s-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

# 3. Firewall
resource "google_compute_firewall" "internal" {
  name    = "allow-internal"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
  }
  allow {
    protocol = "udp"
  }
  allow {
    protocol = "icmp"
  }
  source_ranges = ["10.240.0.0/24"]
}

resource "google_compute_firewall" "ssh" {
  name    = "allow-ssh-gateway"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["gateway"]
}

# 4. Instances

# Gateway (Bastion)
resource "google_compute_instance" "gateway" {
  name         = "gateway"
  machine_type = "e2-medium"
  zone         = var.zone
  tags         = ["gateway"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.subnet.name
    access_config {
      # Laisse vide pour obtenir une IP publique éphémère
    }
  }

  metadata = {
    ssh-keys = "ubuntu:${tls_private_key.ssh_key.public_key_openssh}"
  }
}

# Master
resource "google_compute_instance" "master" {
  name         = "master"
  machine_type = "e2-standard-2"
  zone         = var.zone
  tags         = ["master"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 50
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.subnet.name
    network_ip = "10.240.0.10"
  }

  metadata = {
    ssh-keys = "ubuntu:${tls_private_key.ssh_key.public_key_openssh}"
  }
}

# Workers (3 VMs)
resource "google_compute_instance" "worker" {
  count        = 3
  name         = "worker-${count.index}"
  machine_type = "e2-standard-4"
  zone         = var.zone
  tags         = ["worker"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 100
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.subnet.name
  }

  metadata = {
    ssh-keys = "ubuntu:${tls_private_key.ssh_key.public_key_openssh}"
  }
}