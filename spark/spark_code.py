# this is the spark code that will receive rows from kafka trhough topic 'events_logs'
# and process them using pyspark
import joblib
import numpy as np
import pandas as pd

# ....
# some spark code 
# ....


label_mapping = {
    'Normal': 0,
    'Generic': 1,
    'Exploits': 2,
    'Fuzzers': 3,
    'DoS': 4,
    'Reconnaissance': 5,
    'Analysis': 6,
    'Backdoor': 7,
    'Shellcode': 8,
    'Worms': 9
}

# block of code on how to deal with a received message from kafka
def process_message(message):
    """
    message is a dict with the structure from the producer_code.py file:
    """
    # turn the dict into a dataframe row using df
    row_df = pd.DataFrame([message]) # evertything about conversions can be changed bcs idk the specifics of spark :)

    feature_names = [name.lower() for name in row_df.columns]
    feature_names = [name.replace('sintpkt', 'sinpkt').replace('dintpkt', 'dinpkt').replace('smeansz', 'smean').replace('dmeansz', 'dmean').replace('res_bdy_len', 'response_body_len') for name in feature_names]
    row_df.columns = feature_names
    # drop unecessary columns
    row_df = row_df.drop(columns=['srcip', 'sport', 'dstip', 'dsport', 'stime', 'ltime'])
    # add this column (well it's necessary)
    row_df['rate'] = np.nan
    # reorder columns
    right_order_of_columns = [
        'dur', 'proto', 'service', 'state', 'spkts', 'dpkts', 'sbytes',
       'dbytes', 'rate', 'sttl', 'dttl', 'sload', 'dload', 'sloss', 'dloss',
       'sinpkt', 'dinpkt', 'sjit', 'djit', 'swin', 'stcpb', 'dtcpb', 'dwin',
       'tcprtt', 'synack', 'ackdat', 'smean', 'dmean', 'trans_depth',
       'response_body_len', 'ct_srv_src', 'ct_state_ttl', 'ct_dst_ltm',
       'ct_src_dport_ltm', 'ct_dst_sport_ltm', 'ct_dst_src_ltm',
       'is_ftp_login', 'ct_ftp_cmd', 'ct_flw_http_mthd', 'ct_src_ltm',
       'ct_srv_dst', 'is_sm_ips_ports', 'attack_cat', 'label'
    ]
    row_df = row_df[right_order_of_columns]

    # data ready for inference
    df_data_to_inference = row_df.drop(columns=['attack_cat', 'label'])
    y_truth_binary = row_df['label']
    y_truth_category = row_df['attack_cat']

    return df_data_to_inference, y_truth_binary, y_truth_category

def preprocessing_data(df_data_to_inference):
    label_encoders_import = joblib.load('./pretrained_models/label_encoders_binary_class.pkl')
    label_encoders_multi_import = joblib.load('./pretrained_models/label_encoders_multi_class.pkl')

    df_data_to_binary_classification = df_data_to_inference.copy()
    df_data_to_multi_classification = df_data_to_inference.copy()

    categorical_cols_multi = ['proto', 'service', 'state']
    categorical_cols_binary = ['proto', 'service', 'state']

    for col in categorical_cols_binary:
        # Map unseen test values to 'Unknown' before transforming
        le_binary = label_encoders_import[col]
        df_data_to_binary_classification[col] = df_data_to_binary_classification[col].apply(
            lambda x: x if x in le_binary.classes_ else 'Unknown'
        )
        df_data_to_binary_classification[col] = le_binary.transform(df_data_to_binary_classification[col])

    for col in categorical_cols_multi:
        le_multi = label_encoders_multi_import[col]
        df_data_to_multi_classification[col] = df_data_to_multi_classification[col].apply(
            lambda x: x if x in le_multi.classes_ else 'Unknown'
        )
        df_data_to_multi_classification[col] = le_multi.transform(df_data_to_multi_classification[col])

    return df_data_to_binary_classification, df_data_to_multi_classification

def preprocessing_truth_multi(y_truth_category):
    
    y_truth_category_mapped = y_truth_category.map(label_mapping)
    y_truth_category.fillna(label_mapping['Normal'], inplace=True)
    return y_truth_category_mapped

def main():
    # code to receive messages from kafka topic 'events_logs'
    # for each received message, call process_message(message)
    received_messages = []  # This should be replaced with actual Kafka message receiving logic

    # import models 
    model_binary = joblib.load('./pretrained_models/xgboost_unsw_nb15_model_binary_class.pkl')
    model_multi = joblib.load('./pretrained_models/xgboost_unsw_nb15_model_multi_class.pkl')

    for message in received_messages:
        df_data_to_inference, y_truth_binary, y_truth_category = process_message(message)

        df_data_to_binary_classification, df_data_to_multi_classification = preprocessing_data(df_data_to_inference)
        y_truth_category = preprocessing_truth_multi(y_truth_category)

        # inference on binary classification model
        y_pred_binary = model_binary.predict(df_data_to_binary_classification)

        # inference on multi-class classification model
        y_pred_multi = model_multi.predict(df_data_to_multi_classification)

        # TODO: maybe calculate accuracy or other metrics here

        # append to the message the predictions and TODO: send it to be saved elsewhere (juste preparing the dict) 
        message['y_pred_binary'] = y_pred_binary
        message['y_pred_cat_attack'] = y_pred_multi
        message['y_pred_cat_attack_label'] = y_pred_multi.map(label_mapping) # reverse mapping to get the string label
    