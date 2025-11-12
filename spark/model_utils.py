import joblib
import pandas as pd
import sklearn
import xgboost


def load_model(name):
    return joblib.load(f"./pretrained_models/{name}")


class BinaryClassificationModel:
    def __init__(self, encoder_model, classifier_model):
        self.label_encoders = encoder_model
        self.classifier = classifier_model

    def predict(self, X_values):
        try:
            categorical_cols_binary = ['proto', 'service', 'state']
            label_encoders_binary_import = self.label_encoders

            # Encode categorical columns in csv_test_set
            for col in categorical_cols_binary:
                le_binary = label_encoders_binary_import[col]
                # Map unseen test values to 'Unknown' before transforming
                X_values[col] = X_values[col].apply(
                    lambda x: x if x in le_binary.classes_ else 'Unknown'
                )
                X_values[col] = le_binary.transform(X_values[col])

            y_values_pred = self.classifier.predict(X_values)
            print(f"!!!!!!!!!! PREDICTION  {y_values_pred} !!!!!!!!!!")
        except ValueError as e:
            print(f"!!!!!!!!!! PREDICTION FAILED: {e} !!!!!!!!!!")
            y_values_pred = None
        return y_values_pred
