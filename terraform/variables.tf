variable "project" {
  default = "apt-subset-427519-g1" 
}


variable "region" {
  description = "The region to deploy to"
  default     = "europe-west1"  # Belgique (St. Ghislain)
}

variable "zone" {
  description = "The zone to deploy to"
  default     = "europe-west1-b" # Zone B en Belgique
}