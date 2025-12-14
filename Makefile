# ====== Variables ======
NS ?= default
K  := minikube kubectl --  -n $(NS)

KAFKA_DIR   := apache_kafka
SPARK_DIR   := spark
PRODUCER_DIR:= python_producer

.PHONY: start-minikube start-kafka start-spark-pods start_python_producer \
        launch_producer submit_spark_job status pf-master pf-driver stop-minikube \
        delete-resources nuke

# ------- Cluster -------
start-minikube:
	minikube start --driver=docker --memory=6096 --cpus=8
	# (optionnel mais utile pour les PVC dynamiques)
	minikube addons enable storage-provisioner || true
	minikube addons enable default-storageclass || true
	minikube addons enable metrics-server || true

# ------- Kafka (contrôleurs -> brokers) -------
start-kafka:
	$(K) apply -f $(KAFKA_DIR)/kafka_controller_statefulset.yaml
	$(K) wait --for=condition=ready pod -l app=kafka-controller --timeout=300s
	$(K) apply -f $(KAFKA_DIR)/kafka_broker_statefulset.yaml
	$(K) wait --for=condition=ready pod -l app=kafka-broker --timeout=300s
	$(K) apply -f $(KAFKA_DIR)/topic_job.yaml
	$(K) wait --for=condition=complete job/kafka-topic-creator --timeout=300s

# ------- Spark (master -> workers -> client) -------
start-spark-pods:
	$(K) apply -f $(SPARK_DIR)/spark_master_deployment.yaml
	$(K) rollout status deploy/spark-master --timeout=180s
	$(K) apply -f $(SPARK_DIR)/spark_worker_deployment.yaml
	$(K) rollout status deploy/spark-worker --timeout=300s
	$(K) apply -f $(SPARK_DIR)/spark_client_statefulset.yaml
	$(K) wait --for=condition=ready pod -l app=spark-client --timeout=180s

# ------- Producteur Python -------
start_python_producer:
	$(K) apply -f $(PRODUCER_DIR)/producer_deployment.yaml
	$(K) rollout status deploy/python-producer --timeout=300s
	$(K) logs -f deployment/python-producer

# ------- Job Spark -------
submit_spark_job:
	# copie le job et le script de submit dans le pod client
	minikube kubectl -- -n $(NS) cp $(SPARK_DIR)/spark_job.py spark-client-0:/opt/spark/work-dir/spark_job.py
	minikube kubectl -- -n $(NS) cp $(SPARK_DIR)/model_utils.py spark-client-0:/opt/spark/work-dir/model_utils.py
	minikube kubectl -- -n $(NS) cp $(SPARK_DIR)/pretrained_models/ spark-client-0:/opt/spark/work-dir/pretrained_models/

	minikube kubectl -- -n $(NS) cp $(SPARK_DIR)/spark_submit.sh spark-client-0:/opt/spark/work-dir/spark_submit.sh
	# lance le job (peut prendre du temps la 1ère fois : téléchargement des packages)
	$(K) exec -it spark-client-0 -- /bin/bash /opt/spark/work-dir/spark_submit.sh


# ============================================
# MONITORING TARGETS (Added by Wail)
# ============================================

setup-monitoring:
	kubectl create namespace monitoring || echo "Namespace already exists"
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || echo "Repo already added"
	helm repo update
	helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack --namespace monitoring --set prometheus.prometheusSpec.retention=30d --set grafana.adminPassword=admin --set grafana.service.type=NodePort --wait --timeout=10m
	@echo "=========================================="
	@echo "Monitoring deployed successfully!"
	@echo "Access Grafana: make access-grafana"
	@echo "Then open: http://localhost:3000"
	@echo "Username: admin | Password: admin"
	@echo "=========================================="

access-grafana:
	@echo "Opening Grafana at http://localhost:3000"
	@echo "Username: admin | Password: admin"
	kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

access-prometheus:
	@echo "Opening Prometheus at http://localhost:9090"
	kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090

delete-monitoring:
	helm uninstall kube-prometheus-stack -n monitoring || echo "Stack not found"
	kubectl delete namespace monitoring || echo "Namespace not found"
	
# ------- Aides -------
status:
	@echo "== Pods ==" && $(K) get pods -o wide
	@echo "== PVC =="  && $(K) get pvc
	@echo "== Services ==" && $(K) get svc

pf-master:
	# UI Master sur http://localhost:8080
	minikube kubectl -- -n $(NS) port-forward svc/spark-master-service 8080:8080

pf-driver:
	# UI Driver sur http://localhost:4040
	minikube kubectl -- -n $(NS) port-forward pod/spark-client-0 4040:4040

# ------- Stop/Clean -------
stop-minikube:
	minikube stop

# Supprime ce que tu as créé via apply (propre)
delete-resources:
	-$(K) delete -f $(KAFKA_DIR)/kafka_broker_statefulset.yaml
	-$(K) delete -f $(KAFKA_DIR)/kafka_controller_statefulset.yaml
	-$(K) delete -f $(KAFKA_DIR)/topic_job.yaml
	-$(K) delete -f $(SPARK_DIR)/spark_client_statefulset.yaml
	-$(K) delete -f $(SPARK_DIR)/spark_worker_deployment.yaml
	-$(K) delete -f $(SPARK_DIR)/spark_master_deployment.yaml
	-$(K) delete -f $(PRODUCER_DIR)/producer_deployment.yaml

# GROS reset (attention: détruit aussi les PVC)
nuke:
	-minikube kubectl -- -n $(NS) delete all --all
	-minikube kubectl -- -n $(NS) delete pvc --all
