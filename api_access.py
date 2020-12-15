import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime


class SolarCheck:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.meters = "https://webapi.meetdata.nl/api/1/meters"
        self.measurements = "https://webapi.meetdata.nl/api/1/measurements/"
        self.authorization = HTTPBasicAuth(self.username, self.password)
        self.main = "https://webapi.meetdata.nl/api/1/"

    def check_credentials(self):
        r = requests.post(self.meters, auth=self.authorization)
        return r.status_code == 200

    def get_all_meters(self):
        """
        If connection is ok than let the data trhough
        :return:
        """
        r = requests.post(self.meters, auth=self.authorization)
        if r.status_code == 200:
            return True, r.json()
        else:
            return False, r.json()

    def get_daily(self, connection_id: int, metering_point: int, year: int, month: int, day: int):
        """
        Get daily values for metering point
        """
        api = self.measurements + f"{connection_id}/" + f"{metering_point}/" + f"{year}/" + f"{month}/" + f"{day}"
        r = requests.post(api, auth=self.authorization)
        if r.status_code == 200:
            return r.json()
        else:
            return "api error"

    def get_monthly(self, connection_id, metering_point: int, year: int, month: int):
        api = self.measurements + f"{connection_id}/" + f"{metering_point}/" + f"{year}/" + f"{month}"
        r = requests.post(api, auth=self.authorization)
        if r.status_code == 200:
            return r.json()
        else:
            return "api error"

    @staticmethod
    def process_metering_point_data(data: list):
        """
        Process response from metering data
        """
        human = str()
        for d in data:
            actual_date = datetime.fromtimestamp(d["timestamp"])
            constr = f"{actual_date} origin: {d['origin']} status:{d['status']} Value:{d['value']}\n"
            human += constr
        return human

    @staticmethod
    def process_mettering_points(metering_points: list):
        """
        Process meter points to be used for further queries
        :param metering_points:
        :return:
        """
        ids = list()
        for point in metering_points:
            requested_point = {
                "meteringPointId": point["meteringPointId"],
                "channels": point["channels"]

            }
            ids.append(requested_point)

        return ids

    @staticmethod
    def make_data_frame(data: list, column_name: str) -> pd.DataFrame:
        """
        Creates dataframe for the list of dictionaries
        :param data: list of dictionaries
        :param column_name: Name of the column you would like to assign
        :return:
        """
        # convert from unix to human readable
        for stat in data:
            actual_date = datetime.fromtimestamp(stat["timestamp"])
            stat["snapshot"] = actual_date
        df = pd.DataFrame.from_dict(data)
        df.drop(['origin', 'status', 'timestamp'], axis=1, inplace=True)
        df.set_index("snapshot", inplace=True)
        df.rename({'value': column_name}, axis='columns', inplace=True)
        return df

    @staticmethod
    def filter_data_frame(data: list, column_name: str, start_date, end_date):
        for stat in data:
            stat["snapshot"] = datetime.fromtimestamp(stat["timestamp"])
            stat.pop("origin")
            stat.pop("status")
        df = pd.DataFrame.from_dict(data)
        df.loc[:, 'timestamp'] = df.timestamp.apply(lambda x: datetime.fromtimestamp(x).date())
        mask = (df['timestamp'] > start_date) & (
                df['timestamp'] <= end_date)
        filtered_df = df.loc[mask]
        filtered_df.drop(['timestamp'], axis=1, inplace=True)
        filtered_df.set_index("snapshot", inplace=True)
        filtered_df.rename({'value': column_name}, axis='columns', inplace=True)
        return filtered_df
