
import json
import time
import random
from confluent_kafka import Producer
import pandas as pd
import numpy as np
import subprocess

p = Producer({
    "bootstrap.servers": "kafka-broker-0.kafka-broker-service:19092",
    "enable.idempotence": True,
    "acks": "all",
})
csv_files = ['UNSW-NB15_1.csv', 'UNSW-NB15_2.csv', 'UNSW-NB15_3.csv', 'UNSW-NB15_4.csv']

def on_delivery(err, msg):
    if err:
        print(f"❌ Delivery failed: {err}")
    else:
        print(f"✅ Delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")

# NOTE: you will need to download these files from this link and put them in the same directory as this script
# download link:
url = "https://mega.nz/folder/EYcF3I7A#shlgKrU69INQxKbrZdDBxQ"
destination = "./"
subprocess.run(["mega-get", url, destination])
try:
    file_idx = 0
    features_pd = pd.read_csv('./events_logs_dataset/NUSW-NB15_features.csv',encoding='utf-8', encoding_errors='ignore')
    ## take the column 'Name', it is the feature/column names for the csv files
    feature_names = features_pd['Name'].tolist()
    ml_dataset = ['id', 'dur', 'proto', 'service', 'state', 'spkts', 'dpkts', 'sbytes',
       'dbytes', 'rate', 'sttl', 'dttl', 'sload', 'dload', 'sloss', 'dloss',
       'sinpkt', 'dinpkt', 'sjit', 'djit', 'swin', 'stcpb', 'dtcpb', 'dwin',
       'tcprtt', 'synack', 'ackdat', 'smean', 'dmean', 'trans_depth',
       'response_body_len', 'ct_srv_src', 'ct_state_ttl', 'ct_dst_ltm',
       'ct_src_dport_ltm', 'ct_dst_sport_ltm', 'ct_dst_src_ltm',
       'is_ftp_login', 'ct_ftp_cmd', 'ct_flw_http_mthd', 'ct_src_ltm',
       'ct_srv_dst', 'is_sm_ips_ports', 'attack_cat', 'label']
    while True:
        # read csv file
        csv_file = csv_files[file_idx]
        csv_file_df = pd.read_csv(f"./events_logs_dataset/{csv_file}", header=None)
        feature_names = [name.lower() for name in feature_names]
        feature_names = [name.replace('sintpkt', 'sinpkt').replace('dintpkt', 'dinpkt').replace('smeansz', 'smean').replace('dmeansz', 'dmean').replace('res_bdy_len', 'response_body_len') for name in feature_names]
        csv_file_df.columns = feature_names
        csv_file_df['rate'] = np.nan
        csv_file_df = csv_file_df.reindex(columns=ml_dataset, fill_value=0)
        csv_file_df = csv_file_df.drop(columns=["attack_cat", "label", "id"]) # i was hesitating whether to drop these two columns or not

        for index, row in csv_file_df.iterrows():
            log = row.to_dict() # see below to know the structure of this dict message
            # order = {
            #     "order_id": f"o-{int(time.time())}",
            #     "amount": round(random.uniform(5.0, 100.0), 2)
            # }
            print("sent order:", log)
            p.produce(
                    topic="demo",
            #         key=order["order_id"],
                    value=json.dumps(log).encode(),
                    callback=on_delivery
                )
            p.poll(0)
            time.sleep(1) if index % 10 == 0 else None

        file_idx += 1
        if file_idx >= len(csv_files):
            file_idx = 0

except KeyboardInterrupt:
    print("Stopping producer...")
finally:
    p.flush()