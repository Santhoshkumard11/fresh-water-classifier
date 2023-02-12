import logging
import numpy as np

from helpers.constants import model_attr

from tensorflow.keras.models import load_model
from tensorflow.python.keras.backend import set_session

import tensorflow as tf
import keras.backend.tensorflow_backend as tb
tb._SYMBOLIC_SCOPE.value = True



MODEL_PATH = 'models/classifier_30.model'

# Load your trained model
global graph
graph = tf.get_default_graph()

# set the session state for detection
session = tf.Session()
set_session(session)

# load the model and get the model running for prediction
model = load_model(MODEL_PATH)
model._make_predict_function()

# label reference
classifier_classes_dict = {0: "safe to consume ", 1: "unsafe to consume"}


class Predictor:
    def __init__(self, features_dict: list, model_version="latest") -> None:
        self.features_dict = features_dict
        self.model_version = model_version

    def get_model_attr(self):
        
        model_attributes = model_attr.get(self.model_version)
        model_version = model_attributes.get("model_name")
        
        if self.model_version == "latest":
            model_attr.get(model_attributes)


    def preprocess_feature_list(self):
        pass


    def predict(self):
        """ Make predictions by loading the image into the session

        Returns:
            str: return the classification
        """

        try:
            logging.info("Attempting to make prediction..")

            predict_output = ""

            features_dict = self.preprocess_feature_list()

            # set the default graph again
            with graph.as_default():
                # set the same session for prediction
                set_session(session)
                predict_output = model.predict(features_dict)
                predicted_class = predict_output.tolist()[0]

            final_detected_type = classifier_classes_dict.get(
                int(predicted_class), "error")

            logging.info('Prediction made successfully!!!')

        except Exception as e:
            logging.exception(f"An error occurred while prediction: {e}")
            raise

        return final_detected_type
