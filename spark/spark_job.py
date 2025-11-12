import joblib
import pandas as pd
import sklearn
import xgboost
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, pandas_udf, struct
from pyspark.sql.types import StructType, StringType, DoubleType, IntegerType, FloatType, StructField

from model_utils import BinaryClassificationModel, load_model


fields = [
    ("proto", StringType()),
    ("state", StringType()),
    ("dur", FloatType()),
    ("sbytes", IntegerType()),
    ("dbytes", IntegerType()),
    ("sttl", IntegerType()),
    ("dttl", IntegerType()),
    ("sloss", IntegerType()),
    ("dloss", IntegerType()),
    ("service", StringType()),
    ("sload", FloatType()),
    ("dload", FloatType()),
    ("spkts", IntegerType()),
    ("dpkts", IntegerType()),
    ("swin", IntegerType()),
    ("dwin", IntegerType()),
    ("stcpb", IntegerType()),
    ("dtcpb", IntegerType()),
    ("smean", IntegerType()),
    ("dmean", IntegerType()),
    ("trans_depth", IntegerType()),
    ("response_body_len", IntegerType()),
    ("sjit", FloatType()),
    ("djit", FloatType()),
    ("sinpkt", FloatType()),
    ("dinpkt", FloatType()),
    ("tcprtt", FloatType()),
    ("synack", FloatType()),
    ("ackdat", FloatType()),
    ("is_sm_ips_ports", IntegerType()),
    ("ct_state_ttl", IntegerType()),
    ("ct_flw_http_mthd", IntegerType()),
    ("is_ftp_login", IntegerType()),
    ("ct_ftp_cmd", IntegerType()),
    ("ct_srv_src", IntegerType()),
    ("ct_srv_dst", IntegerType()),
    ("ct_dst_ltm", IntegerType()),
    ("ct_src_ltm", IntegerType()),
    ("ct_src_dport_ltm", IntegerType()),
    ("ct_dst_sport_ltm", IntegerType()),
    ("ct_dst_src_ltm", IntegerType()),
]
schema = StructType([StructField(name, dtype, True) for name, dtype in fields])



    

if __name__ == "__main__":
    # Spark session
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

    logs_df = logs_raw.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    logs_df = logs_df.fillna(0)

    encoder_model = load_model("label_encoders_binary_class.pkl")
    classifier_model = load_model("xgboost_unsw_nb15_model_binary_class.pkl")

    classification_model = BinaryClassificationModel(encoder_model, classifier_model)
    broadcasted_model = spark.sparkContext.broadcast(classification_model)

    @pandas_udf(returnType=IntegerType())
    def predict_with_model(X_values_batch: pd.DataFrame) -> pd.Series:
        model = broadcasted_model.value
        predictions = model.predict(X_values_batch)

        if predictions is None:
            return pd.Series([None] * len(X_values_batch))
        else:
            return pd.Series(predictions)

    predictions_df = logs_df.withColumn(
        "label",
        predict_with_model(struct(*[col(c) for c, dtype in fields]))
    )

    query = (
        predictions_df.writeStream
        .format("console")
        .outputMode("append")
        .option("truncate", False)
        .option("checkpointLocation", "/tmp/checkpoints/logs-stream")  # shared folder or local
        .start()
    )

    query.awaitTermination()

