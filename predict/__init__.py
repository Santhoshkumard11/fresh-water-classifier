import logging
import azure.functions as func
from time import time
import json
from helpers.predictor import Predictor
from helpers.mysql_client import MySQLClient


def mysql_handler(req_body: dict, response: dict, query_type: str):
    """Handle MySQL related operations

    Args:
        req_body (dict): request body from the user
        response (dict): response to be sent to the user
        query_type (str): the type of query to be executes
    """

    mysql_client = MySQLClient()

    if query_type == "ml_model_log":
        mysql_client.add_ml_logs(req_body, response)
    if query_type == "misclassified":
        mysql_client.add_misclassified(req_body, response)


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Fresh Water Classifier endpoint called..")
    start_time, end_time = time(), 0

    try:
        if req.method == "POST":
            req_body = req.get_json()

            features_list = req_body.get("features_dict", [])
            mode = req_body.get("mode", "predict")
            skip_db_update = req_body.get("skip_db_update", False)

            if mode == "predict":
                # check if we have feature dict before doing predictions
                if len(features_list) == 0:
                    end_time = round(time() - start_time, 4)
                    return func.HttpResponse(
                        f"""Endpoint hit!\nPass the features_list in the json body for classification. Response Time - {end_time}""",
                        status_code=200,
                    )
                else:
                    predictor_obj = Predictor(features_list, req_body)
                    prediction_result = predictor_obj.predict()

                    end_time = round(time() - start_time, 4)

                    prediction_result.update(
                        {"response_time": end_time, "log_source": "azure"}
                    )

                    if skip_db_update is False:
                        mysql_handler(req_body, prediction_result, "ml_model_log")

                    return func.HttpResponse(
                        json.dumps(prediction_result),
                        status_code=200,
                    )

            elif mode == "model_describe":
                predictor_obj = Predictor(features_list, req_body)
                model_result = predictor_obj.model_describe()

                end_time = round(time() - start_time, 4)
                model_result.update({"response_time": end_time, "log_source": "azure"})

                return func.HttpResponse(json.dumps(model_result), status_code=200)

            elif mode == "misclassified":
                predictor_obj = Predictor(features_list, req_body)
                model_result = predictor_obj.model_describe()

                end_time = round(time() - start_time, 4)
                model_result.update({"response_time": end_time, "log_source": "azure"})

                if skip_db_update is False:
                    mysql_handler(req_body, model_result, "misclassified")
                return func.HttpResponse(json.dumps(model_result), status_code=200)

            else:
                end_time = round(time() - start_time, 4)
                return func.HttpResponse(
                    f"Send a POST request mode in ('predict', 'model_describe', 'misclassified'). Response Time - {end_time}",
                    status_code=200,
                )

        else:
            end_time = round(time() - start_time, 4)
            return func.HttpResponse(
                f"Endpoint hit! Please send a POST request with all the required columns to predict. Response Time - {end_time}",
                status_code=200,
            )

    except Exception as e:
        logging.exception(f"Here is the error: \n{e}")
        end_time = round(time() - start_time, 4)
        return func.HttpResponse(
            f"Something went wrong during detection. Response Time - {end_time}"
        )

    finally:
        logging.info(f"Fresh Water Classification Ended in {end_time}s")
