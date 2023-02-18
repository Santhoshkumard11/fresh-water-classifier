import logging
import azure.functions as func
from time import time
import json
from helpers.predictor import Predictor
from helpers.mysql_client import MySQLClient


def add_time_to_response(response, end_time):
    from io import StringIO

    string_io = StringIO((response))
    response_json = json.load(string_io)
    response_json.update({"response_time": end_time, "log_source": "azure"})
    return json.dumps(response_json)


def mysql_handler(req_body: dict, response: str, query_type: str):
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

            features_list = req_body.get("features_dict")
            mode = req_body.get("mode", "predict")
            skip_db_update = req_body.get("skip_db_update", False)

            if mode == "predict":
                end_time = round(time() - start_time, 4)
                if len(features_list) == 0:
                    return func.HttpResponse(
                        f"""Endpoint hit! \n
                            Pass the features_list in the json body for classification. Response Time - {end_time}""",
                        status_code=200,
                    )
                else:
                    predictor_obj = Predictor(features_list, req_body)
                    prediction_result = predictor_obj.predict()
                    end_time = round(time() - start_time, 4)
                    prediction_result = add_time_to_response(
                        prediction_result, end_time
                    )
                    if skip_db_update is False:
                        mysql_handler(req_body, prediction_result, "ml_model_log")
                    return func.HttpResponse(
                        prediction_result,
                        status_code=200,
                    )
            elif mode == "model_describe":
                predictor_obj = Predictor(features_list, req_body)
                model_result = predictor_obj.model_describe()
                end_time = round(time() - start_time, 4)
                model_result = add_time_to_response(model_result, end_time)
                return func.HttpResponse(model_result, status_code=200)
            elif mode == "misclassified":
                predictor_obj = Predictor(features_list, req_body)
                model_result = predictor_obj.model_describe()
                end_time = round(time() - start_time, 4)
                model_result = add_time_to_response(model_result, end_time)
                if skip_db_update is False:
                    mysql_handler(req_body, model_result, "misclassified")
                return func.HttpResponse(model_result, status_code=200)
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
