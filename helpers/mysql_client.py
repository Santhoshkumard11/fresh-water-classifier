import mysql.connector
import os
import logging
from helpers.constants import (
    ML_LOG_QUERY_ARGS_MAPPING,
    MISCLASSIFIED_QUERY_ARGS_MAPPING,
    QUERY_CONSTRUCT_HELPER,
    INSERT_QUERY_TEMPLATE,
)

logging.info(f'host - {os.environ.get("MYSQL_HOST")}')


# create the connection object and connect with MySQL database
MYSQL_CONN = mysql.connector.connect(
    host=os.environ.get("MYSQL_HOST"),
    user=os.environ.get("MYSQL_USERNAME"),
    password=os.environ.get("MYSQL_PASSWORD"),
    port=3306,
    database="ml_model_logs",
    autocommit=True,
)


class MySQLClient:
    def __init__(self) -> None:
        self.column_values, self.query_type, self.final_query_to_execute = [], "", ""

    def load_request_response_dicts(self, req_body: dict, response: dict):
        """Initialize both request and response dicts

        Args:
            req_body (dict): request body from user
            response (dict): response to be sent to user
        """

        self.req_body = req_body
        self.response = response

    def construct_query(self):
        """Construct the complete query to be execute in the MySQL server"""

        query_helper = QUERY_CONSTRUCT_HELPER[self.query_type]

        database_name, table_name, column_names = (
            query_helper.get("database_name"),
            query_helper.get("table_name"),
            query_helper.get("column_names"),
        )

        self.get_column_values()

        final_column_value = str(self.column_values)[1:-1].replace(
            "'default'", "default"
        )

        self.final_query_to_execute = INSERT_QUERY_TEMPLATE.format(
            database_name=database_name,
            table_name=table_name,
            column_names=column_names,
            column_values=final_column_value,
        )

        logging.info(f"query - {self.final_query_to_execute}")

    def execute_query(self):
        """Where the actual execution of the query happens"""

        try:
            with MYSQL_CONN.cursor() as cur:
                cur.execute(self.final_query_to_execute)
                logging.info(f"{self.query_type} - executed query!")

        except Exception as e:
            logging.error(f"Error in execute_query - {e}")
            logging.info(f"Query - {self.final_query_to_execute}")
            raise

    def get_column_values(self):
        """Get all the column values needed to be inserted into MySQL database"""

        query_args_mapper = (
            ML_LOG_QUERY_ARGS_MAPPING
            if self.query_type == "ml_model_logs"
            else MISCLASSIFIED_QUERY_ARGS_MAPPING
        )

        # iterate through the mapper and toggle between dicts
        for list_value in query_args_mapper.values():
            _from, column_value_name = list_value
            if _from == "req_body":
                value = self.req_body.get(column_value_name, "default")
                if column_value_name == "features_dict":
                    value = f'"{value}"'
                self.column_values.append(value)
            if _from == "response":
                self.column_values.append(
                    self.response.get(column_value_name, "default")
                )

    def add_ml_logs(self, req_body: dict, response: dict):
        """Start the process to add ml model metrics to MySQL database

        Args:
            req_body (dict): request body from user
            response (dict): response to be sent to user
        """

        self.column_values = []
        self.query_type = "ml_model_logs"
        self.load_request_response_dicts(req_body, response)
        self.construct_query()
        self.execute_query()

    def add_misclassified(self, req_body: dict, response: dict):
        """Start the process to add misclassified request to MySQL database

        Args:
            req_body (dict): request body from user
            response (dict): response to be sent to user
        """

        self.column_values = []
        self.query_type = "misclassified"
        self.load_request_response_dicts(req_body, response)
        self.construct_query()
        self.execute_query()
