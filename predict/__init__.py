import logging
import azure.functions as func
from helpers.predictor import Predictor


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Fresh Water Classifier endpoint called..")

    try:
        if req.method == "POST":
            req_body = req.get_json()

            features_list = req_body.get("features_dict")
            mode = req_body.get("mode", "predict")

            if mode == "predict":
                if len(features_list) == 0:
                    return func.HttpResponse(
                        """Endpoint hit! \n
                            Pass the features_list in the json body for classification""",
                        status_code=200,
                    )
                else:
                    predictor_obj = Predictor(features_list, req_body)
                    prediction_result = predictor_obj.predict()

                    return func.HttpResponse(
                        prediction_result,
                        status_code=200,
                    )
            elif mode == "model_describe":
                predictor_obj = Predictor(features_list, req_body)
                model_result = predictor_obj.model_describe()
                return func.HttpResponse(model_result, status_code=200)
            else:
                return func.HttpResponse(
                    "Send a POST request mode in ('predict', 'model_describe') ",
                    status_code=200,
                )

        else:
            return func.HttpResponse(
                "Endpoint hit! Please send a POST request with all the required columns to predict",
                status_code=200,
            )

    except Exception as e:
        logging.exception(f"Here is the error: \n{e}")
        return func.HttpResponse("Something went wrong during detection")

    finally:
        logging.info("Fresh Water Classification Ended.")
