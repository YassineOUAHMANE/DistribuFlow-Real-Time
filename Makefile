# this makefile may not work on Windows
# execute in this order to start the full pipeline:

start-minikube:
	minikube start --driver=docker --memory=4096 --cpus=2

# make take a while to download the images and start the pods
start-kafka:
	kubectl apply -f apache_kafka/kafka_broker_statefulset.yaml
	kubectl apply -f apache_kafka/kafka_controller_statefulset.yaml

# make take a while to download the images and start the pods
start-spark-pods:
	kubectl apply -f spark/spark_master_deployment.yaml
	kubectl apply -f spark/spark_worker_deployment.yaml
	kubectl apply -f spark/spark_client_statefulset.yaml

start_python_producer:
	kubectl apply -f python_producer/producer_pod.yaml

launch_producer:
	#copy the producer.py into the producer pod
	kubectl cp python_producer/producer.py python-producer:/producer.py
	#execute the producer.py inside the producer pod
	# keep it running to continuously produce messages to Kafka
	kubectl exec -it python-producer -- python3 /producer.py

submit_spark_job:
	#copy the spark_job.py into the spark-client pod
	kubectl cp spark/spark_job.py spark-client-0:/opt/spark/work-dir/spark_job.py
	kubectl cp spark/model_utils.py spark-client-0:/opt/spark/work-dir/model_utils.py
	kubectl cp spark/pretrained_models/ spark-client-0:/opt/spark/work-dir/pretrained_models/
	kubectl cp spark/spark_submit.sh spark-client-0:/opt/spark/work-dir/spark_submit.sh
	#execute the spark_job.py inside the spark-client pod
	#may take a while to execute (download dependencies, connect to master, dag scheduling, etc)
	# it will process new message as they arrive in Kafka topic
	# if no more message, it will just wait for new messages
	kubectl exec -it spark-client-0 -- /bin/bash /opt/spark/work-dir/spark_submit.sh

stop-minikube:
	minikube stop

delete-resources:
	kubectl delete all --all

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