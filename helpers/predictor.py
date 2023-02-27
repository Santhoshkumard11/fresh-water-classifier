import logging
import pandas as pd
import joblib
import numpy as np

from helpers.utils import get_model_attributes

# from sklearnex import patch_sklearn
# patch_sklearn()

BASE_MODEL_PATH = "models"

# Download all the models and store it in cache when the function starts
MODEL_V1_PATH = f"{BASE_MODEL_PATH}/rf_v1.1.sav"

MODEL_V2_PATH = f"{BASE_MODEL_PATH}/rf_v2.0.sav"

MODEL_V3_PATH = f"{BASE_MODEL_PATH}/rf_v3.1.sav"

# load the model and get the model running for prediction
MODEL_V1 = joblib.load(MODEL_V1_PATH)
MODEL_V2 = joblib.load(MODEL_V2_PATH)
MODEL_V3 = joblib.load(MODEL_V3_PATH)

logging.info("Models loaded successfully! Ready for predictions")

# label reference
CLASSIFIER_CLASSES_MAPPING_DICT = {0: "safe to consume", 1: "unsafe to consume"}


class Predictor:
    "Class that makes the prediction and other ML model operations"

    def __init__(self, features_dict: dict, req_body={}) -> None:
        self.features_dict = features_dict
        self.req_body = req_body

        self.model_version, self.flag_probability = req_body.get(
            "model_version", "latest"
        ), req_body.get("get_probability", False)

        self.flag_model_features, self.flag_feature_importance = req_body.get(
            "get_model_features", False
        ), req_body.get("get_feature_importance", False)

        self.model_attributes = get_model_attributes(self.model_version)

        self.model_version = self.model_attributes["model_version"]

        logging.info(f"Using model version - {self.model_version}")

        self.predict_df = pd.DataFrame()

        # switch between different versions of the model
        if self.model_version == "v1.1":
            self.model = MODEL_V1
        elif self.model_version == "v2.0":
            self.model = MODEL_V2
        elif self.model_version == "v3.1":
            self.model = MODEL_V3

    def add_missed_out_columns(self):
        """Add the feature columns created by pandas dummies method"""

        model_features_list = self.model_attributes["features_list"]

        df_column_names = self.predict_df.columns.to_list()

        # iterate through the models features
        for column_name in model_features_list:
            if column_name not in df_column_names:
                self.predict_df[column_name] = [0]

    def preprocess_feature_list(self):
        """Place where we create dummies for feature columns and do the extensive preprocessing"""

        for key, value in self.features_dict.items():
            # skip categorical feature columns
            if key not in ["Color", "Month", "Source"]:
                self.features_dict.update({key: float(value)})

        self.predict_df = pd.DataFrame(self.features_dict, index=[0])

        if self.model_version == "v2.0":
            self.predict_df = pd.get_dummies(
                self.predict_df, prefix=["clr", "src"], columns=["Color", "Source"]
            ).drop(columns=["Month"])
            self.add_missed_out_columns()
            numerical_columns_to_fill_median = list(
                self.predict_df._get_numeric_data().columns
            )

            for column_name in numerical_columns_to_fill_median:
                column_median = self.predict_df[column_name].median()
                self.predict_df[column_name] = (
                    self.predict_df[column_name]
                    .replace(np.NaN, column_median)
                    .round(10)
                )

        if self.model_version == "v3.1":
            self.predict_df = pd.get_dummies(
                self.predict_df, prefix=["clr"], columns=["Color"]
            ).drop(columns=["Month", "Source"])
            self.add_missed_out_columns()
            numerical_columns_to_fill_median = list(
                self.predict_df._get_numeric_data().columns
            )

            for column_name in numerical_columns_to_fill_median:
                column_median = self.predict_df[column_name].median()
                self.predict_df[column_name] = (
                    self.predict_df[column_name]
                    .replace(np.NaN, column_median)
                    .round(10)
                )

    def construct_final_output(self, predicted_class: int) -> dict:
        """Construct the final output to be sent to user

        Args:
            predicted_class (int): the predicted class

        Returns:
            dict: final response dict
        """

        final_output = {}

        raw_prediction = CLASSIFIER_CLASSES_MAPPING_DICT.get(
            int(predicted_class), "error"
        )

        final_output.update(
            {"prediction": raw_prediction, "predicted_class": predicted_class}
        )

        if self.flag_probability:
            probability = self.model.predict_proba(self.predict_df).tolist()[0]

            final_output.update(
                {"probability": {"0": probability[0], "1": probability[1]}}
            )

        if self.flag_model_features:
            final_output.update(
                {"feature_columns": self.model.feature_names_in_.tolist()}
            )

        if self.flag_feature_importance:
            final_output.update(
                {"feature_importance": self.model.feature_importances_.tolist()}
            )

        return final_output

    def model_describe(self):
        """Construct the model describe dict

        Returns:
            dict: model describe dict
        """

        final_output = {}

        for key, value in zip(
            self.model.feature_names_in_.tolist(),
            self.model.feature_importances_.tolist(),
        ):
            final_output.update({key: value})

        return {"feature_importance": final_output}

    def predict(self):
        """Make predictions by loading the image into the session

        Returns:
            str: return the classification
        """

        try:
            logging.info("Attempting to make prediction..")

            predict_output = ""

            self.preprocess_feature_list()

            predict_output = self.model.predict(self.predict_df)

            predicted_class = predict_output.tolist()[0]

            logging.info(f"class - {predicted_class}")

            logging.info("Prediction made successfully!!!")

        except Exception as e:
            logging.exception(f"An error occurred while prediction: {e}")
            raise

        return self.construct_final_output(predicted_class)
