FROM apache/spark:3.5.0


USER root
RUN apt-get update && apt-get install -y wget && \
    mkdir -p /opt/spark/jars/ && \
    wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.0/spark-sql-kafka-0-10_2.12-3.5.0.jar && \
    wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.1/kafka-clients-3.4.1.jar && \
    wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.0/spark-token-provider-kafka-0-10_2.12-3.5.0.jar && \
    apt-get remove -y wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3.9 -m pip install --no-cache-dir -r /tmp/requirements.txt


# Spark containers often run as 'spark' user, switch back:
USER spark
ENV PYSPARK_PYTHON=/usr/bin/python
ENV PYSPARK_DRIVER_PYTHON=/usr/bin/python


CMD ["sleep", "infinity"]