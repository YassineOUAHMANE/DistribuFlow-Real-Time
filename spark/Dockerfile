FROM apache/spark:3.5.0


USER root
RUN apt-get update && \
    apt-get install -y python3.9 python3.9-distutils python3.9-dev python3.9-venv curl && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.9 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3.9 -m pip install --no-cache-dir -r /tmp/requirements.txt


# Spark containers often run as 'spark' user, switch back:
USER spark
ENV PYSPARK_PYTHON=/usr/bin/python
ENV PYSPARK_DRIVER_PYTHON=/usr/bin/python


CMD ["sleep", "infinity"]