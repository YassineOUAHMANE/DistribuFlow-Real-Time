export SPARK_LOG_LEVEL=WARN

/opt/spark/bin/spark-submit \
  --master spark://spark-master-service.default.svc.cluster.local:7077 \
  --conf spark.pyspark.python=/usr/bin/python \
  --conf spark.pyspark.driver.python=/usr/bin/python \
  --conf spark.driver.host=spark-client-0.spark-client-service.default.svc.cluster.local \
  --conf spark.driver.port=8081 \
  --deploy-mode client \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --name "testApp" \
  --py-files model_utils.py \
  spark_job.py