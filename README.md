# Déploiment sur GCP

Ce projet déploie une architecture complète de traitement de données en temps réel sur Google Cloud Platform (GCP). Il utilise **Terraform** pour l'infrastructure, **Ansible** pour la configuration, et **Kubernetes** pour l'orchestration des conteneurs (Kafka & Spark).

---

## Partie 1 : Configuration Locale

Ces étapes provisionnent les VMs et installent les dépendances logicielles.

### 1. Déploiement de l'infrastructure (Terraform)
```bash
cd infra/terraform
terraform apply
# Tapez 'yes' pour confirmer.
# ⚠️ IMPORTANT : Notez les IPs affichées à la fin (Gateway & Master).
```
### 2. Configuration des machines (Ansible)

Installation de Docker, Kubernetes et des outils réseaux.

```bash
cd ../config
# La variable ANSIBLE_HOST_KEY_CHECKING=False évite les blocages liés aux nouvelles clés SSH
ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i inventory.ini playbook.yml
```

### 3. Préparation SSH & Transfert de fichiers

Utilisation de l'agent SSH pour faciliter le passage par la Gateway.

```bash
# Charger la clé dans l'agent
eval $(ssh-agent -s)
ssh-add config/id_rsa_gcp

# Copier le projet vers le Master (via la Gateway)
# Remplacer <IP_GATEWAY> et <IP_MASTER> par les vraies valeurs
scp -r -J ubuntu@<IP_GATEWAY> apache_kafka/ python_producer/ scripts/ spark/ ubuntu@<IP_MASTER>:~/project
```

### 4. Connexion au Master

```bash
ssh -A -J ubuntu@<IP_GATEWAY> ubuntu@<IP_MASTER>
```

## Partie 2 : Configuration du Cluster (Sur le Master)

Toutes les commandes suivantes s'exécutent dans le terminal du Master.

```bash
cd ~/project
```

### 1. Initialisation du Stockage & Réseau

Indispensable pour que Kafka puisse stocker ses données et que les pods communiquent.

```bash
# Installer le provisionneur de stockage local
kubectl apply -f [https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml](https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml)

# Définir ce stockage comme "default"
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

# Redémarrer le DNS (Correctif Firewall GCP)
kubectl delete pod -n kube-system -l k8s-app=kube-dns
```

### 2. Déploiement des Services

Apache Kafka :

```bash
kubectl apply -f apache_kafka/kafka_controller_statefulset.yaml
kubectl apply -f apache_kafka/kafka_broker_statefulset.yaml
```

Apache Spark :

```bash
kubectl apply -f spark/spark_master_deployment.yaml
kubectl apply -f spark/spark_worker_deployment.yaml
kubectl apply -f spark/spark_client_statefulset.yaml
```

Producteur de Données :

```bash
kubectl apply -f app-data/python_producer/producer_pod.yaml
```

## Partie 3 : Préparation des Jobs

Injection des scripts Python et des modèles ML dans les Pods actifs.
###1. Configuration du Client Spark

```bash
kubectl cp spark/spark_submit.sh spark-client-0:/opt/spark/work-dir/spark_submit.sh
kubectl cp spark/spark_job.py spark-client-0:/opt/spark/work-dir/spark_job.py
kubectl cp spark/model_utils.py spark-client-0:/opt/spark/work-dir/model_utils.py
kubectl cp spark/pretrained_models/ spark-client-0:/opt/spark/work-dir/pretrained_models/
```

### 2. Configuration du Producteur

```bash
kubectl cp python_producer/producer.py python-producer:/producer.py
```

## Partie 4 : Exécution (Démo)

Ouvrez deux terminaux connectés au Master pour visualiser le flux en temps réel.

**Terminal A :** Lancer le Traitement Spark (Consommateur)

Ce job va lire les données depuis Kafka et appliquer le modèle de prédiction.

```bash
kubectl exec -it spark-client-0 -- /bin/bash /opt/spark/work-dir/spark_submit.sh
```

**Terminal B :** Lancer la Production de Données

Ce script génère des logs et les envoie dans Kafka.

```bash
kubectl exec -it python-producer -- python3 /producer.py
```

## 🚑 Dépannage

Si les Pods Kafka restent bloqués en statut Pending, lancez un nettoyage complet des volumes :

```bash
kubectl delete pod kafka-broker-0 kafka-controller-0
kubectl delete pvc --all
# Les pods redémarreront automatiquement avec le nouveau stockage.
```


