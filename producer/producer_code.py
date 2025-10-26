"""
read the csv files and produce messages to Kafka topic (the kafaka or producer parts can be changed, 
but the reading of csv and assigning column names should be kept as is)
"""
import json
import pandas as pd
from kafka import KafkaProducer
import time

producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))


topic_name = 'events_logs'
csv_files = ['UNSW-NB15_1.csv', 'UNSW-NB15_2.csv', 'UNSW-NB15_3.csv', 'UNSW-NB15_4.csv']
# NOTE: you will need to download these files from this link and put them in the same directory as this script
# download link: https://mega.nz/folder/EYcF3I7A#shlgKrU69INQxKbrZdDBxQ

features_pd = pd.read_csv('NUSW-NB15_features.csv',encoding='utf-8', encoding_errors='ignore')
## take the column 'Name', it is the feature/column names for the csv files
feature_names = features_pd['Name'].tolist()

for csv_file in csv_files:
    # read one file at a time
    csv_file_df = pd.read_csv(csv_file, header=None)
    csv_file_df.columns = feature_names
    #csv_file_df = csv_file_df.drop(columns=["attack_cat", "label"]) # i was hesitating whether to drop these two columns or not

    # iterate through each row and send to kafka topic
    # TODO: this code should be changed to this specs:
    # 1. should be able to configure the rate of sending rows (e.g., rows per second)
    # 2. should re do the sending if we've gone through all files (should be continuous)
    for index, row in csv_file_df.iterrows():
        message = row.to_dict() # see below to know the structure of this dict message
        producer.send(topic_name, value=message)
        time.sleep(1) # change it if you want

producer.flush()

"""
structure of message dict: (descriptions of other columns can be found in NUSW-NB15_features.csv)
{
  "srcip": "nominal",
  "sport": "integer",
  "dstip": "nominal",
  "dsport": "integer",
  "proto": "nominal",
  "state": "nominal",
  "dur": "Float",
  "sbytes": "Integer",
  "dbytes": "Integer",
  "sttl": "Integer",
  "dttl": "Integer",
  "sloss": "Integer",
  "dloss": "Integer",
  "service": "nominal",
  "Sload": "Float",
  "Dload": "Float",
  "Spkts": "integer",
  "Dpkts": "integer",
  "swin": "integer",
  "dwin": "integer",
  "stcpb": "integer",
  "dtcpb": "integer",
  "smeansz": "integer",
  "dmeansz": "integer",
  "trans_depth": "integer",
  "res_bdy_len": "integer",
  "Sjit": "Float",
  "Djit": "Float",
  "Stime": "Timestamp",
  "Ltime": "Timestamp",
  "Sintpkt": "Float",
  "Dintpkt": "Float",
  "tcprtt": "Float",
  "synack": "Float",
  "ackdat": "Float",
  "is_sm_ips_ports": "Binary",
  "ct_state_ttl": "Integer",
  "ct_flw_http_mthd": "Integer",
  "is_ftp_login": "Binary",
  "ct_ftp_cmd": "integer",
  "ct_srv_src": "integer",
  "ct_srv_dst": "integer",
  "ct_dst_ltm": "integer",
  "ct_src_ltm": "integer",
  "ct_src_dport_ltm": "integer",
  "ct_dst_sport_ltm": "integer",
  "ct_dst_src_ltm": "integer",
  "attack_cat": "nominal",      # In this data set , nine categories e.g. Fuzzers, Analysis, Backdoors, DoS Exploits, Generic, Reconnaissance, Shellcode and Worms"
  "Label": "binary"             # 0 for normal, 1 for attack
}
"""