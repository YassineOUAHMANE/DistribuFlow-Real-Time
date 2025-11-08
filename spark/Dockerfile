FROM apache/spark:3.5.0


USER root
RUN apt-get update && \
    apt-get install -y python3 python3-distutils python3-venv python3-pip && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    pip3 install --no-cache-dir pyspark==3.5.0 joblib pandas scikit-learn xgboost



# Spark containers often run as 'spark' user, switch back:
USER spark
ENV PYSPARK_PYTHON=/usr/bin/python
ENV PYSPARK_DRIVER_PYTHON=/usr/bin/python


CMD ["sleep", "infinity"]