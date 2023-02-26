import os
from helpers.constants import MODEL_ATTRIBUTES


_LATEST_MODEL_VERSION = os.environ["LATEST_MODEL_VERSION"]


def get_model_attributes(model_version: str) -> dict:
    """Get the model attributes of the current model version

    Args:
        model_version (str): model version from user request body

    Returns:
        dict: model attributes
    """

    MODEL_ATTRIBUTES.update({"latest": MODEL_ATTRIBUTES[_LATEST_MODEL_VERSION]})

    return MODEL_ATTRIBUTES[model_version]
