"""Module to interface with the INSEE SDMX Data"""

import calendar
import requests
import xml.etree.ElementTree as eT

from datetime import datetime
from dateutil.parser import parse
from io import BytesIO

import pandas as pd

from ..datashelf import DataShelf


class INSEE:
    """Class to interface with the INSEE SDMX"""

    def __init__(self):
        """Initialize the class"""
        self.__data_shelf = DataShelf().insee()
        self.__data_flows = self.__refresh_data_flow_list()
        self.__data = self.__retrieve_data
        self.__series_revisions = self.__retrieve_revisions_for_series
        self.__all_code_lists = self.__show_whole_code_list
        # self.__data_flow_cl = self.__get_code_list_for_data_flow

    def __refresh_data_flow_list(self):
        """
        Refresh the list of the data flows
        :return: a DataFrame with the list of the available data flows
        :rtype: pd.DataFrame
        """
        url = self.__data_shelf["data_flow_list"]
        insee_data_flows = requests.get(url).content
        output = list()
        for _, element in eT.iterparse(BytesIO(insee_data_flows)):
            if element.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}Dataflows":
                for data_flow in element:
                    data_flow_id = data_flow.attrib["id"]
                    data_flow_description = None
                    number_of_series = None
                    for annotation in data_flow:
                        if annotation.attrib and "en" in \
                                annotation.attrib["{http://www.w3.org/XML/1998/namespace}lang"]:
                            data_flow_description = annotation.text
                        if annotation.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common}Annotations":
                            for sub_annotation in annotation:
                                for information in sub_annotation:
                                    if "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common}AnnotationText":
                                        number_of_series = information.text.split(":")[1]
                    output.append([data_flow_id, data_flow_description, number_of_series])
        return pd.DataFrame(data=output, columns=["DataFlowID", "DataFlowDescription", "NumberOfSeries"]).\
            set_index("DataFlowID")

    def __retrieve_data(self, data_flow, kwargs=None):
        """
        Retrieve data given a data flow and some optional parameters
        :param str data_flow: a data flow among the list of all maintained in the INSEE database
        :param dict kwargs: optional parameters to customize the query
        :return: a DataFrame with the requested data, if any
        :rtype: pd.DataFrame
        """
        formatted_inputs = ""
        if kwargs:
            validated_inputs = [i for i in list(kwargs.keys()) if self.__data_shelf['inputs'].get(i)]
            formatted_inputs = "&".join(
                [self.__data_shelf['inputs'].get(i).format(kwargs[i]) for i in validated_inputs]
                                        )
        validated_data_flow = True if data_flow.upper() in list(self.__data_flows.index) else False
        if not validated_data_flow:
            raise ValueError(f"The value needs to be included in the list of available Data Flows: "
                             f"{list(self.__data_flows.index)}")
        url = "?".join([self.__data_shelf['data'].format(data_flow), formatted_inputs]) if formatted_inputs \
            else self.__data_shelf['data'].format(data_flow)
        downloaded_data = requests.get(url).content
        results = self.__extract_data_from_tags(downloaded_data)
        return results

    def __extract_data_from_tags(self, file_content):
        """
        Extract the data from the downloaded DSD
        :param bytes file_content: file to be processed
        :return: a DataFrame with the parsed DSD
        :rtype: pd.DataFrame
        """
        output = list()
        series_columns = None
        obs_columns = None
        for _, element in eT.iterparse(BytesIO(file_content)):
            if element.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message}DataSet":
                for series in element:
                    series_columns = list(series.attrib.keys())
                    series_data = list(series.attrib.values())
                    for obs in series:
                        obs_columns = list(obs.attrib.keys())
                        obs_data = list(obs.attrib.values())
                        if obs_data:
                            output.append(series_data + obs_data)
        results = pd.DataFrame(data=output, columns=series_columns + obs_columns).set_index("IDBANK")
        results["TIME_PERIOD"].apply(lambda x: self.__convert_ecb_time_format_to_datetime(x))
        return results

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

    def __retrieve_revisions_for_series(self, id_bank):
        """
        Retrieve the revisions for a single series given an id_bank
        :param str id_bank: an INSEE identifier unique to series
        :return: a DataFrame with the information requested, if any
        :rtype: pd.DataFrame
        """
        url = self.__data_shelf['include_history'].format(id_bank)
        insee_download = requests.get(url).content
        output = list()
        series_columns = None
        obs_columns = None
        for _, element in eT.iterparse(BytesIO(insee_download)):
            if element.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message}DataSet":
                valid_from = element.attrib["validFromDate"]
                action = element.attrib["action"]
                for series in element:
                    series_columns = list(series.attrib.keys())
                    series_data = list(series.attrib.values())
                    for obs in series:
                        obs_columns = ["TIME_PERIOD", "OBS_VALUE", "OBS_STATUS", "OBS_QUAL", "OBS_TYPE"]
                        obs_values = [obs.attrib[i] for i in obs_columns]
                        obs_values = obs_values + [valid_from, action]
                        if obs_values:
                            output.append(series_data + obs_values)
        results = pd.DataFrame(data=output,
                               columns=series_columns + obs_columns + ["ValidFromDate", "Action"]).set_index("IDBANK")
        results["TIME_PERIOD"].apply(lambda x: self.__convert_ecb_time_format_to_datetime(x))
        return results

    def __show_whole_code_list(self):
        """
        Show the whole code list from the INSEE
        :return: a DataFrame with the requested information
        :rtype: pd.DataFrame
        """
        url = self.__data_shelf['code_list']
        insee_download = requests.get(url).content
        output = list()
        for _, element in eT.iterparse(BytesIO(insee_download)):
            if element.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}Codelists":
                for code_list in element:
                    code_list_id = code_list.attrib["id"]
                    code_list_name = None
                    code_desc = None
                    for name in code_list:
                        if name.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common}Name":
                            if name.attrib and "en" in name.attrib["{http://www.w3.org/XML/1998/namespace}lang"]:
                                code_list_name = name.text
                        if name.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}Code":
                            code_id = name.attrib["id"]
                            for sub_name in name:
                                if sub_name.attrib and \
                                        "en" in sub_name.attrib["{http://www.w3.org/XML/1998/namespace}lang"]:
                                    code_desc = sub_name.text
                            output.append([code_list_id, code_list_name, code_id, code_desc])
        results = pd.DataFrame(data=output,
                               columns=["CodeListID", "CodeListDescription", "CodeID", "CodeDescription"]
                               ).set_index("CodeListID")
        return results

    def show_data_flows(self):
        """
        Show Data Flows publicly
        :return: a DataFrame with the list of the Data Flows
        :rtype: pd.DataFrame
        """
        return self.__data_flows

    def retrieve_data(self):
        """
        Call the function to retrieve data from the INSEE SDMX database
        :return: a DataFrame with the list of available DSD
        :rtype: function
        """
        return self.__data

    def retrieve_series_revision(self):
        """
        Call the function to retrieve the revisions for a series
        :return: a DataFrame with the parsed revisions, if any
        :rtype: function
        """
        return self.__series_revisions

    def get_all_code_lists(self):
        """
        Get all the code lists for all the data flows available in the INSEE database
        :return: a DataFrame with all the codelists
        :rtype: pd.DataFrame
        """
        self.__show_whole_code_list()
