import sqlite3
from typing import Any, Union

from loguru import logger


class Database:
    """
    Basic class describing the database
    Args:
        path_to_do (str): the path to the database
    """

    def __init__(self, path_to_db='data/main.db'):
        self.path_to_db = path_to_db

    @property
    def connection(self):
        """
        Creating a connection with the database
        """
        return sqlite3.connect(self.path_to_db)

    def execute(self, sql_request: str, parameters: tuple = None,
                fetchone=False, fetchall=False, commit=False):
        """
        Sending a database SQL request
        :param sql_request: SQL command
        :param parameters: SQL request parameters
        :param fetchone: return the first entry
        :param fetchall: return the all entries in the form of a list
        :param commit: make changes to the base
        """
        if not parameters:
            parameters = tuple()
        connection = self.connection
        connection.set_trace_callback(log)
        cursor = connection.cursor()
        data = None
        cursor.execute(sql_request, parameters)
        if commit:
            connection.commit()
        if fetchone:
            data = cursor.fetchone()
        if fetchall:
            data = cursor.fetchall()
        connection.close()
        return data

    def create_table_users(self) -> None:
        """
        Creating a table Users.
        Information about users.
        """
        sql_request = """
        CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY NOT NULL,
        user_name VARCHAR(255) NOT NULL,
        connection_date TIMESTAMP NOT NULL
        );
        """
        self.execute(sql_request, commit=True)

    def create_table_user_requests(self) -> None:
        """
        Creating a table UserRequests.
        Information about request parameters when searching for hotels.
        """
        sql_requests = """
        CREATE TABLE IF NOT EXISTS UserRequests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date_request TIMESTAMP NOT NULL,
        type_search city VARCHAR(255) NOT NULL,
        city VARCHAR(255),
        area_id INTEGER,
        area_name VARCHAR(255),
        latitude FLOAT,
        longitude FLOAT,
        amount_hotels INTEGER NOT NULL,
        has_photo VARCHAR(255) NOT NULL,
        amount_photos INTEGER NOT NULL,
        check_in VARCHAR(255) NOT NULL,
        check_out VARCHAR(255) NOT NULL,
        price_min INTEGER NOT NULL,
        price_max INTEGER NOT NULL,
        center_min INTEGER NOT NULL,
        center_max INTEGER NOT NULL,
        FOREIGN KEY(user_id) REFERENCES Users(id)
        );
        """
        self.execute(sql_requests, commit=True)

    def create_table_hotel(self) -> None:
        """
        Creating a table Hotel.
        Information about hotels.
        """
        sql_requests = """
        CREATE TABLE IF NOT EXISTS Hotel(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        request_id INTEGER NOT NULL,
        date_report TIMESTAMP NOT NULL,
        hotel_id INTEGER NOT NULL,
        name VARCHAR(255) NOT NULL,
        address VARCHAR(255) NOT NULL,
        center VARCHAR(255) NOT NULL,
        price VARCHAR(255) NOT NULL,
        photos VARCHAR(255),
        FOREIGN KEY(user_id) REFERENCES Users(id)
        FOREIGN KEY(request_id) REFERENCES UserRequests(id)
        );
        """
        self.execute(sql_requests, commit=True)

    def create_table_callback(self) -> None:
        """
        Creating a table Callback.
        The table contains the areas names and the unique keys corresponding to them.
        """
        sql_requests = """
        CREATE TABLE IF NOT EXISTS Callback(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        callback_code VARCHAR(255) NOT NULL,
        area_name VARCHAR(255) NOT NULL
        );
        """
        self.execute(sql_requests, commit=True)

    def add_user(self, id_user: int, name: str, connection_date: str) -> None:
        """
        Adding a user to the Users table
        """
        sql_request = 'INSERT INTO Users(id, user_name, connection_date) VALUES(?, ?, ?)'
        parameters = (id_user, name, connection_date)
        self.execute(sql_request, parameters=parameters, commit=True)

    def add_user_request(self, user_id: int, date_request: str, type_search: str, city: Any, area_id: Any,
                         area_name: Any, latitude: Any, longitude: Any, amount_hotels: int, has_photo: str,
                         amount_photos: int, check_in: str, check_out: str, price_min: Any, price_max: Any,
                         center_min: Any, center_max: Any) -> None:
        """
        Adding a request to the UserRequests table
        """
        sql_request = 'INSERT INTO UserRequests(id, user_id, date_request, type_search, city, area_id, area_name, ' \
                      'latitude, longitude, amount_hotels, has_photo, amount_photos, check_in, check_out, price_min, ' \
                      'price_max, center_min, center_max) ' \
                      'VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        parameters = (user_id, date_request, type_search, city, area_id, area_name, latitude, longitude, amount_hotels,
                      has_photo, amount_photos, check_in, check_out, price_min, price_max, center_min, center_max)
        self.execute('PRAGMA foreign_keys = ON')
        self.execute(sql_request, parameters=parameters, commit=True)

    def add_hotel_report(self, user_id: int, request_id: int, date_report: str, hotel_id: int, name: str,
                         address: str, center: str, price: str, photos: str) -> None:
        """
        Adding a hotel to the Hotel table
        """
        sql_request = 'INSERT INTO Hotel(id, user_id, request_id, date_report, hotel_id, name, address, center, ' \
                      'price, photos) VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        parameters = (user_id, request_id, date_report, hotel_id, name, address, center, price, photos)
        self.execute('PRAGMA foreign_keys = ON')
        self.execute(sql_request, parameters=parameters, commit=True)

    def add_callback(self, callback_code: str, area_name: str) -> None:
        """
        Adding a callback information to the Callback table
        """
        sql_request = 'INSERT INTO Callback(id, callback_code, area_name) VALUES(NULL, ?, ?)'
        parameters = (callback_code, area_name)
        self.execute(sql_request, parameters=parameters, commit=True)

    @staticmethod
    def format_args(sql_request, parameters: dict) -> Union[str, tuple]:
        """
        Formatting parameters for SQL request
        """
        sql_request += " AND ".join([f'{item} = ?' for item in parameters])
        return sql_request, tuple(parameters.values())

    def get_request_id(self, **kwargs) -> None:
        """
        Receiving a request id from the UserRequests table
        """
        sql_request = 'SELECT id FROM UserRequests WHERE '
        sql_request, parameters = self.format_args(sql_request, kwargs)
        return self.execute(sql_request, parameters, fetchone=True)

    def get_report_hotel(self, **kwargs) -> None:
        """
        Receiving hotels information from the Hotel table
        """
        sql_request = 'SELECT * FROM Hotel WHERE '
        sql_request, parameters = self.format_args(sql_request, kwargs)
        return self.execute(sql_request, parameters, fetchall=True)

    def get_callback(self, **kwargs) -> None:
        """
        Receiving callbacks information from the Callback table
        """
        sql_request = 'SELECT area_name FROM Callback WHERE '
        sql_request, parameters = self.format_args(sql_request, kwargs)
        return self.execute(sql_request, parameters, fetchone=True)

    def get_requests(self, **kwargs):
        """
        Receiving requests information from the UserRequests table
        """
        sql_request = 'SELECT * FROM UserRequests WHERE '
        sql_request, parameters = self.format_args(sql_request, kwargs)
        return self.execute(sql_request, parameters, fetchall=True)

    def delete_hotels(self, **kwargs):
        """
        Removing information about hotels from the Hotel table
        """
        sql_request = 'DELETE FROM Hotel WHERE '
        sql_request, parameters = self.format_args(sql_request, kwargs)
        return self.execute(sql_request, parameters, commit=True)

    def delete_request(self, **kwargs):
        """
        Removing information about requests from the UserRequests table
        """
        sql_request = 'DELETE FROM UserRequests WHERE '
        sql_request, parameters = self.format_args(sql_request, kwargs)
        return self.execute(sql_request, parameters, commit=True)


def log(statement):
    """ Logging SQL requests """
    logger.info(statement)
