import logging
import pandas as pd

from helpers.utils import get_model_attributes

import joblib
import json

MODEL_PATH = "models/96_90_random_forest_nor_10k.sav"


# load the model and get the model running for prediction
model = joblib.load(MODEL_PATH)

# label reference
classifier_classes_dict = {0: "safe to consume", 1: "unsafe to consume"}


class Predictor:
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

        self.predict_df = None

    def preprocess_feature_list(self):
        for key, value in self.features_dict.items():
            self.features_dict.update({key: float(value)})

        self.predict_df = pd.DataFrame(self.features_dict, index=[0])

    def construct_final_output(self, predicted_class: int):
        final_output = {}

        raw_prediction = classifier_classes_dict.get(int(predicted_class), "error")

        final_output.update(
            {"prediction": raw_prediction, "prediction_class": predicted_class}
        )

        if self.flag_probability:
            probability = model.predict_proba(self.predict_df).tolist()[0]

            final_output.update(
                {"probability": {"0": probability[0], "1": probability[1]}}
            )

        if self.flag_model_features:
            final_output.update({"feature_columns": model.feature_names_in_.tolist()})

        if self.flag_feature_importance:
            final_output.update(
                {"feature_importance": model.feature_importances_.tolist()}
            )

        return json.dumps(final_output)

    def model_describe(self):
        final_output = {}

        for key, value in zip(model.feature_names_in_.tolist(), model.feature_importances_.tolist()):
            final_output.update({key: value})

        return json.dumps({"feature_importance":final_output})

    def predict(self):
        """Make predictions by loading the image into the session

        Returns:
            str: return the classification
        """

        try:
            logging.info("Attempting to make prediction..")

            predict_output = ""

            self.preprocess_feature_list()

            predict_output = model.predict(self.predict_df)

            predicted_class = predict_output.tolist()[0]

            logging.info(f"class - {predicted_class}")

            logging.info("Prediction made successfully!!!")

        except Exception as e:
            logging.exception(f"An error occurred while prediction: {e}")
            raise

        return self.construct_final_output(predicted_class)
