from helpers.constants import model_attributes


def get_model_attributes(model_version: str) -> dict:
    model_attributes.update({"latest": model_attributes.get("v2")})

    return model_attributes.get(model_version)
