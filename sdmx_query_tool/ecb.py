"""Module to interface with the ECB SDMX portal"""

import calendar
import requests
import xml.etree.ElementTree as eT

from datetime import datetime
from dateutil.parser import parse
from io import BytesIO

import pandas as pd

from .datashelf import DataShelf


class ECB:
    """Class containing the SDMX instructions for the ECB"""

    def __init__(self):
        """Initialize the class"""
        self.__datashelf = DataShelf().ecb()
        self.__dsd = self.__refresh_dsd_list()
        self.__data = self.__retrieve_data

    def __refresh_dsd_list(self):
        """
        Show the list of DSDs maintained by the ECB
        :return: a DataFrame with the list of DSDs
        :rtype: pd.DataFrame
        """
        url = f"{self.__datashelf['endpoint']['protocol']}{self.__datashelf['endpoint']['wsEntryPoint']}" \
              f"{self.__datashelf['endpoint']['datastructure']}ECB?references=dataflow"
        data = requests.get(url)
        tree = eT.parse(BytesIO(data.content))
        dsd = dict()
        for elem in tree.findall(".//{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}Dataflow"):
            if elem.attrib["agencyID"] == "ECB":
                dsd[elem.attrib["id"]] = None
                for elem1 in elem:
                    if elem1.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common}Name":
                        dsd[elem.attrib["id"]] = elem1.text
        return pd.DataFrame(data=list(dsd.values()), index=list(dsd.keys()), columns=["DSDs"])

    def __retrieve_data(self, dsd, **kwargs):
        """
        Retrieve the data given a combination of inputs
        :param str dsd: name of the dsd to get the data for
        :param dict kwargs: accepted arguments are: start_period, end_period, last_n_observations, first_n_observations,
        updated_after, detail, include_history. For more details on how to use these arguments visit:
        https://sdw-wsrest.ecb.europa.eu/help/
        :return: a DataFrame with the query result, if valid
        :rtype: pd.DataFrame
        """
        validated_inputs = [i for i in list(kwargs.keys()) if self.__datashelf['inputs'].get(i)]
        formatted_inputs = "&".join([self.__datashelf['inputs'].get(i).format(kwargs[i]) for i in validated_inputs])
        validated_dsd = True if dsd.upper() in list(self.__dsd.index) else False
        if not validated_dsd:
            raise ValueError(f"The value needs to be included in the list of available DSDs: {list(self.__dsd.index)}")
        url = f"{self.__datashelf['endpoint']['protocol']}{self.__datashelf['endpoint']['wsEntryPoint']}" \
              f"{self.__datashelf['endpoint']['resource']}{dsd}?{formatted_inputs}"
        downloaded_data = requests.get(url)
        results = pd.DataFrame()
        for _, dataset in eT.iterparse(BytesIO(downloaded_data.content)):
            if dataset.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message}DataSet":
                results = results.append(self.__extract_data_from_tags(dataset))
        results.set_index("seriesId", inplace=True)
        return results

    def __extract_data_from_tags(self, dataset):
        """
        Extract the data from the downloaded DSD
        :param Element dataset: list of series to be parsed
        :return: a DataFrame with the parsed DSD
        :rtype: pd.DataFrame
        """
        output = list()
        action = dataset.attrib["action"]
        valid_from_date = dataset.attrib["validFromDate"]
        list_of_series = dataset.findall(".//{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}Series")
        for sub_series in list_of_series:
            series_key = sub_series.find(".//{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}SeriesKey")
            attributes_key = sub_series.find(
                ".//{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}Attributes")
            obs = sub_series.findall("{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}Obs")
            series_id = ".".join([tag.attrib["value"] for tag in list(series_key)])
            series_attributes = ",".join([tag.attrib["value"] for tag in list(attributes_key)])
            for observation in obs:
                dimension = None
                value = None
                obs_attributes = list()
                for child_obs in list(observation):
                    if child_obs.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}ObsDimension":
                        dimension = self.__convert_ecb_time_format_to_datetime(child_obs.attrib["value"])
                    elif child_obs.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}ObsValue":
                        value = child_obs.attrib["value"]
                    elif child_obs.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic}Attributes":
                        if list(child_obs):
                            obs_attributes.append(child_obs[0].attrib["id"])
                            obs_attributes.append(child_obs[0].attrib["value"])
                output.append([series_id, series_attributes, dimension, value, obs_attributes, action, valid_from_date])
        return pd.DataFrame(data=output,
                            columns=["seriesId", "seriesAttributes", "ObsTime", "ObsValue", "ObsAttributes", "Action",
                                     "ValidFromDate"]
                            )

    def __convert_ecb_time_format_to_datetime(self, time_string):
        """
        Convert the standard ECB date format ISO8601 to datetime
        :param str time_string: string to convert to datetime
        :return: a datetime object
        :rtype: datetime.datetime
        """
        time_string_split = time_string.split("-")
        if len(time_string_split) == 1:
            return parse(time_string + "-12-31")
        elif len(time_string_split) == 2:
            return self.__format_two_parts_date(time_string_split)
        else:
            return parse(time_string)

    def __format_two_parts_date(self, split_date):
        """
        Format a date according to its second part
        :param list split_date: list with the split of the date
        :return: a datetime object
        :rtype: datetime.datetime
        """
        date_suffixes = {
            "S1": "-06-30",
            "S2": "-12-31",
            "Q1": "-03-31",
            "Q2": "-06-30",
            "Q3": "-09-30",
            "Q4": "-12-31"
        }
        year = split_date[0]
        date_tail = split_date[1]
        if date_tail in date_suffixes:
            return parse(year + date_suffixes[date_tail])
        elif "W" in date_tail:
            return datetime.strptime("-".join(split_date) + '-1', "%Y-W%W-%w")
        else:
            last_day = calendar.monthrange(int(year), int(date_tail))[1]
            date = "-".join([year, date_tail, str(last_day)])
            return parse(date)

    def show_dsd(self):
        """
        Show the list of available DSD in the ECB SDMX database
        :return: a DataFrame with the list of available DSD
        :rtype: pd.DataFrame
        """
        return self.__dsd

    def retrieve_data(self):
        """
        Call the function to retrieve data from the ECB SDMX database
        :return: a DataFrame with the list of available DSD
        :rtype: function
        """
        return self.__data
