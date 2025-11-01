
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StringType, DoubleType, IntegerType, FloatType

# 1️⃣ Create Spark session
spark = (
    SparkSession.builder
    .appName("KafkaOrdersStream")
    .getOrCreate()
)


topics_name = "demo"

logs_raw = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "kafka-broker-0.kafka-broker-service:19092")
    .option("subscribe", topics_name)
    .option("startingOffsets", "earliest")  # or earliest
    .load()
)


logs_str = logs_raw.selectExpr(
    "CAST(value AS STRING) as json_str",
    "topic", "partition", "offset", "timestamp"
)


schema = (
    StructType()
    .add("srcip", StringType())
    .add("sport", IntegerType())
    .add("dstip", StringType())
    .add("dsport", IntegerType())
    .add("proto", StringType())
    .add("state", StringType())
    .add("dur", FloatType())
    .add("sbytes", IntegerType())
    .add("dbytes", IntegerType())
    .add("sttl", IntegerType())
    .add("dttl", IntegerType())
    .add("sloss", IntegerType())
    .add("dloss", IntegerType())
    .add("service", StringType())
    .add("Sload", FloatType())
    .add("Dload", FloatType())
    .add("Spkts", IntegerType())
    .add("Dpkts", IntegerType())
    .add("swin", IntegerType())
    .add("dwin", IntegerType())
    .add("stcpb", IntegerType())
    .add("dtcpb", IntegerType())
    .add("smeansz", IntegerType())
    .add("dmeansz", IntegerType())
    .add("trans_depth", IntegerType())
    .add("res_bdy_len", IntegerType())
    .add("Sjit", FloatType())
    .add("Djit", FloatType())
    .add("Stime", IntegerType())
    .add("Ltime", IntegerType())
    .add("Sintpkt", FloatType())
    .add("Dintpkt", FloatType())
    .add("tcprtt", FloatType())
    .add("synack", FloatType())
    .add("ackdat", FloatType())
    .add("is_sm_ips_ports", IntegerType())
    .add("ct_state_ttl", IntegerType())
    .add("ct_flw_http_mthd", IntegerType())
    .add("is_ftp_login", IntegerType())
    .add("ct_ftp_cmd", IntegerType())
    .add("ct_srv_src", IntegerType())
    .add("ct_srv_dst", IntegerType())
    .add("ct_dst_ltm", IntegerType())
    .add("ct_src_ltm", IntegerType())
    .add("ct_src_dport_ltm", IntegerType())
    .add("ct_dst_sport_ltm", IntegerType())
    .add("ct_dst_src_ltm", IntegerType())
)


logs = logs_str.select(
    from_json(col("json_str"), schema).alias("data"),
    "topic", "partition", "offset", "timestamp"
).select(
    col("data.srcip"),
    col("data.sport"),
    col("data.dstip"),
    col("data.dsport"),
    col("data.proto"),
    col("data.state"),
    col("data.dur"),
    col("data.sbytes"),
    col("data.dbytes"),
    col("data.sttl"),
    col("data.dttl"),
    col("data.sloss"),
    col("data.dloss"),
    col("data.service"),
    col("data.Sload"),
    col("data.Dload"),
    col("data.Spkts"),
    col("data.Dpkts"),
    col("data.swin"),
    col("data.dwin"),
    col("data.stcpb"),
    col("data.dtcpb"),
    col("data.smeansz"),
    col("data.dmeansz"),
    col("data.trans_depth"),
    col("data.res_bdy_len"),
    col("data.Sjit"),
    col("data.Djit"),
    col("data.Stime"),
    col("data.Ltime"),
    col("data.Sintpkt"),
    col("data.Dintpkt"),
    col("data.tcprtt"),
    col("data.synack"),
    col("data.ackdat"),
    col("data.is_sm_ips_ports"),
    col("data.ct_state_ttl"),
    col("data.ct_flw_http_mthd"),
    col("data.is_ftp_login"),
    col("data.ct_ftp_cmd"),
    col("data.ct_srv_src"),
    col("data.ct_srv_dst"),
    col("data.ct_dst_ltm"),
    col("data.ct_src_ltm"),
    col("data.ct_src_dport_ltm"),
    col("data.ct_dst_sport_ltm"),
    col("data.ct_dst_src_ltm"),
    "topic", "partition", "offset", "timestamp"
)


query = (
    logs.writeStream
    .format("console")
    .outputMode("append")
    .option("truncate", False)
    .option("checkpointLocation", "/tmp/checkpoints/logs-stream")  # shared folder or local
    .start()
)

query.awaitTermination()