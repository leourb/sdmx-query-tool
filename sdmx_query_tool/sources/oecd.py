"""Module to query for OECD SDMX data"""

import calendar
import requests
import xml.etree.ElementTree as eT

from datetime import datetime
from dateutil.parser import parse
from io import BytesIO
from pprint import pprint

import pandas as pd

from ..datashelf import DataShelf


class OECD:
    """Class to query OECD SDMX data"""

    def __init__(self):
        """Initialize the class"""
        self.__data_shelf = DataShelf().oecd()
        self.__data_flows = self.__refresh_data_flow_list()
        self.__data = self.__retrieve_data
        self.__data_flow_cl = self.__get_code_list_for_data_flow

    def __refresh_data_flow_list(self):
        """
        Refresh the list of the data flows
        :return: a DataFrame with the list of the available data flows
        :rtype: pd.DataFrame
        """
        url = self.__data_shelf["data_flow_list"]
        oecd_data_flows = requests.get(url).content
        output = list()
        for _, element in eT.iterparse(BytesIO(oecd_data_flows)):
            if element.tag == "{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/message}KeyFamilies":
                for single_key in element:
                    if single_key.tag == "{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure}KeyFamily":
                        data_flow_id = single_key.attrib["id"]
                        agency_id = single_key.attrib["agencyID"]
                        data_flow_name = None
                        for name in single_key:
                            if name.attrib and "en" in name.attrib["{http://www.w3.org/XML/1998/namespace}lang"]:
                                data_flow_name = name.text
                                continue
                        output.append([data_flow_id, agency_id, data_flow_name])
        results = pd.DataFrame(data=output, columns=["DataFlowID", "AgencyID", "DataFlowName"]).set_index("DataFlowID")
        return results

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
        for _, element in eT.iterparse(BytesIO(file_content)):
            if element.tag == "{http://oecd.stat.org/Data}Series":
                series_id = ".".join([element.attrib[key] for key in list(element.attrib.keys())])
                for obs in element:
                    obs_time = obs.attrib["TIME"]
                    obs_value = self.__convert_ecb_time_format_to_datetime(obs.attrib["OBS_VALUE"])
                    output.append([series_id, obs_time, obs_value])
        results = pd.DataFrame(data=output, columns=["SeriesID", "ObsTime", "ObsValue"]).set_index("SeriesID")
        results.sort_index(inplace=True)
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

    def __get_code_list_for_data_flow(self, data_flow):
        """
        Return the code-list for a given data flow maintained by the OECD
        :param str data_flow: data flow code to pull up the code list
        :return: a DataFrame with the code list of a given data structure
        :rtype: pd.DataFrame
        """
        if data_flow not in list(self.__data_flows.index):
            raise ValueError(f"Data Flow not found in list. "
                             f"Please select one among: {list(self.__data_flows['DataFlow'])}")
        url = f"{self.__data_shelf['code_list']}{data_flow}"
        code_list_file = requests.get(url).content
        output = list()
        for _, element in eT.iterparse(BytesIO(code_list_file)):
            if element.tag == "{http://www.w3.org/2001/XMLSchema}simpleType":
                code_list_code = element.attrib["name"]
                code_list_desc = None
                for field_type in element:
                    code_list_type = field_type.attrib["base"]
                    for enumeration in field_type:
                        code_list_value = enumeration.attrib["value"]
                        for annotation in enumeration:
                            for documentation in annotation:
                                if "en" in documentation.attrib["{http://www.w3.org/XML/1998/namespace}lang"]:
                                    code_list_desc = documentation.text
                            output.append([code_list_code, code_list_type, code_list_value, code_list_desc])
        results = pd.DataFrame(data=output, columns=["CodeListCode", "CodeListType", "CodeListValue",
                                                     "CodeListDescription"]).set_index("CodeListCode")
        return results

    @staticmethod
    def available_parameters():
        """
        Print the parameters available for the query
        :return: a list with the available parameters
        :rtype: None
        """
        return pprint(list(OECD().__data_shelf['inputs'].keys()))

    def show_data_flows(self):
        """
        Show Data Flows publicly
        :return: a DataFrame with the list of the Data Flows
        :rtype: pd.DataFrame
        """
        return self.__data_flows

    def retrieve_data(self):
        """
        Call the function to retrieve data from the OECD SDMX database
        :return: a DataFrame with the list of available DSD
        :rtype: function
        """
        return self.__data

    def get_code_list_for_data_flow(self):
        """
        Get the code list for a given data flow
        :return: a DataFrame with the code list
        :rtype: function
        """
        return self.__data_flow_cl
