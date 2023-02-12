import logging
import azure.functions as func
from helpers.predictor import Predictor


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Fresh Water Classifier endpoint called..")

    response_message = "Thanks for checking out the api. It works!!"
    try:
        if req.method == "POST":

            req_body = req.get_json()

            features_list, model_version = req_body.get('features_list'), req_body.get("model_version", "latest")

            if len(features_list) == 0:
                return func.HttpResponse(
                    """Thanks for checking out the api. It works!!
                                        Pass the features_list in the json body for classification""",
                    status_code=200)
            else:
                predictor_obj = Predictor(features_list, model_version)
                prediction_result = predictor_obj.predict() 

                return func.HttpResponse(
                    f"The prediction has been made - it's {prediction_result}",
                    status_code=200
                )

        else:

            return func.HttpResponse(
                "Send a POST request with all the required columns.",
                status_code=200)

    except Exception as e:
        logging.exception(f"Here is the error: \n{e}")
        return func.HttpResponse("Something went wrong during detection")

    finally:
        logging.info("Fresh Water Classification Ended")

    return func.HttpResponse(response_message)
