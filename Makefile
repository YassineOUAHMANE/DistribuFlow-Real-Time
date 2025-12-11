
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
