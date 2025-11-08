import joblib
import pandas as pd
import sklearn
import xgboost
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, pandas_udf, struct
from pyspark.sql.types import StructType, StringType, DoubleType, IntegerType, FloatType, StructField

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

def load_model(name):
    return joblib.load(f"./pretrained_models/{name}")


class BinaryClassificationModel:
    def __init__(self):
        self.label_encoders = load_model("label_encoders_binary_class.pkl")
        self.classifier = load_model("xgboost_unsw_nb15_model_binary_class.pkl")

    def predict(self, X_values):
        try:   
            categorical_cols_multi = ['proto', 'service', 'state']
            label_encoders_binary_import = self.label_encoders

            # Encode categorical columns in csv_test_set
            for col in categorical_cols_multi:
                le_binary = label_encoders_binary_import[col]
                # Map unseen test values to 'Unknown' before transforming
                X_values[col] = X_values[col].apply(
                    lambda x: x if x in le_binary.classes_ else 'Unknown'
                )
                X_values[col] = le_binary.transform(X_values[col])
            
            y_values_pred = self.classifier.predict(X_values)
        except ValueError:
            y_values_pred = None
        return y_values_pred


fields = [
    ("srcip", StringType()),
    ("sport", IntegerType()),
    ("dstip", StringType()),
    ("dsport", IntegerType()),
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
    ("Sload", FloatType()),
    ("Dload", FloatType()),
    ("Spkts", IntegerType()),
    ("Dpkts", IntegerType()),
    ("swin", IntegerType()),
    ("dwin", IntegerType()),
    ("stcpb", IntegerType()),
    ("dtcpb", IntegerType()),
    ("smeansz", IntegerType()),
    ("dmeansz", IntegerType()),
    ("trans_depth", IntegerType()),
    ("res_bdy_len", IntegerType()),
    ("Sjit", FloatType()),
    ("Djit", FloatType()),
    ("Stime", IntegerType()),
    ("Ltime", IntegerType()),
    ("Sintpkt", FloatType()),
    ("Dintpkt", FloatType()),
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

logs_df = logs_raw.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")

classification_model = BinaryClassificationModel()
broadcasted_model = spark.sparkContext.broadcast(classification_model)

@pandas_udf(returnType=IntegerType())
def predict_with_model(struct_col_batch: pd.Series) -> pd.Series:
    model = broadcasted_model.value
    X_values = pd.DataFrame(struct_col_batch.tolist())
    predictions = model.predict(X_values)

    if predictions is None:
        return pd.Series([None] * len(X_values))
    else:
        return pd.Series(predictions)
    
predictions_df = logs_df.withColumn(
    "Label",
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