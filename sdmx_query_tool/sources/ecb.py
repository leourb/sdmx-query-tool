"""Module to interface with the ECB SDMX portal"""

import calendar
import requests
import xml.etree.ElementTree as eT

from datetime import datetime
from dateutil.parser import parse
from io import BytesIO

import pandas as pd

from ..datashelf import DataShelf


class ECB:
    """Class containing the SDMX instructions for the ECB"""

    def __init__(self):
        """Initialize the class"""
        self.__data_shelf = DataShelf().oecd()
        self.__data_flows = self.__refresh_data_flow_list()
        self.__data = self.__retrieve_data
        self.__data_flow_cl = self.__get_code_list_for_data_flow

    def __refresh_data_flow_list(self):
        """
        Show the list of data flows maintained by the ECB
        :return: a DataFrame with the list of DSDs
        :rtype: pd.DataFrame
        """
        data_flows_url = f"{self.__data_shelf['endpoint']['protocol']}{self.__data_shelf['endpoint']['wsEntryPoint']}" \
                         f"{self.__data_shelf['endpoint']['dataflow']}ECB"
        data_flows_file = requests.get(data_flows_url).content
        output = list()
        for _, element in eT.iterparse(BytesIO(data_flows_file)):
            if element.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}Dataflows":
                for dsd in element:
                    if dsd.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}Dataflow":
                        dataflow_id = dsd.attrib["id"]
                        dataflow_name = None
                        data_structure_id = None
                        for dsd_name in dsd:
                            if dsd_name.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common}Name":
                                dataflow_name = dsd_name.text
                                continue
                            if dsd_name.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}Structure":
                                for ref in dsd_name:
                                    data_structure_id = ref.attrib["id"]
                        output.append([dataflow_id, dataflow_name, data_structure_id])
        return pd.DataFrame(data=output, columns=["DataFlow", "DataFlowName", "DataStructureCode"]).\
            set_index("DataFlow")

    def __retrieve_data(self, data_flow, **kwargs):
        """
        Retrieve the data given a combination of inputs
        :param str data_flow: name of the dsd to get the data for
        :param dict kwargs: accepted arguments are: start_period, end_period, last_n_observations, first_n_observations,
        updated_after, detail, include_history. For more details on how to use these arguments visit:
        https://sdw-wsrest.ecb.europa.eu/help/
        :return: a DataFrame with the query result, if valid
        :rtype: pd.DataFrame
        """
        validated_inputs = [i for i in list(kwargs.keys()) if self.__data_shelf['inputs'].get(i)]
        formatted_inputs = "&".join([self.__data_shelf['inputs'].get(i).format(kwargs[i]) for i in validated_inputs])
        validated_data_flow = True if data_flow.upper() in list(self.__data_flows.index) else False
        if not validated_data_flow:
            raise ValueError(f"The value needs to be included in the list of available Data Flows: "
                             f"{list(self.__data_flows.index)}")
        url = f"{self.__data_shelf['endpoint']['protocol']}{self.__data_shelf['endpoint']['wsEntryPoint']}" \
              f"{self.__data_shelf['endpoint']['resource']}{data_flow}?{formatted_inputs}"
        downloaded_data = requests.get(url).content
        results = pd.DataFrame()
        for _, dataset in eT.iterparse(BytesIO(downloaded_data)):
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

    @staticmethod
    def get_ecb_code_list():
        """
        Retrieve the whole code-list for all the DSDs maintained by the ECB
        :return: a DataFrame with the whole ECB code-list
        :rtype: pd.DataFrame
        """
        code_list = f"{ECB().__data_shelf['endpoint']['protocol']}{ECB().__data_shelf['endpoint']['wsEntryPoint']}" \
                    f"{ECB().__data_shelf['endpoint']['codelist']}ECB"
        downloaded_cl = requests.get(code_list).content
        code_list_df = pd.DataFrame()
        for _, element in eT.iterparse(BytesIO(downloaded_cl)):
            if element.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}Codelist":
                output_cl = list()
                agency_id = element.attrib["agencyID"]
                cl_parent_id = element.attrib["id"]
                parent_cl_name = None
                cl_id = None
                cl_name = None
                for parent_name in list(element):
                    if parent_name.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common}Name":
                        parent_cl_name = parent_name.text
                        continue
                    if parent_name.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}Code":
                        cl_id = parent_name.attrib["id"]
                        for sub_name in parent_name:
                            cl_name = sub_name.text
                    output_cl.append([agency_id, cl_parent_id, parent_cl_name, cl_id, cl_name])
                code_list_df = code_list_df.append(pd.DataFrame(data=output_cl,
                                                                columns=["AgencyID", "CodeListName",
                                                                         "CodeListDescription", "Code",
                                                                         "CodeDescription"])
                                                   )
        code_list_df.set_index("CodeListName", inplace=True)
        return code_list_df

    def __get_code_list_for_data_flow(self, data_flow):
        """
        Return the code-list for a given data flow maintained by the ECB
        :param str data_flow: data flow code to pull up the code list
        :return: a DataFrame with the code list of a given data structure
        :rtype: pd.DataFrame
        """
        if data_flow not in list(self.__data_flows.index):
            raise ValueError(f"Data Flow not found in list. "
                             f"Please select one among: {list(self.__data_flows['DataFlow'])}")
        data_structure = self.__data_flows.loc[data_flow]["DataStructureCode"]
        code_list_url = f"{self.__data_shelf['endpoint']['protocol']}{self.__data_shelf['endpoint']['wsEntryPoint']}" \
                        f"{self.__data_shelf['endpoint']['datastructure']}ECB/{data_structure}?references=children"
        code_list_file = requests.get(code_list_url).content
        output = list()
        for _, element in eT.iterparse(BytesIO(code_list_file)):
            if element.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}Codelists":
                for cl in element:
                    if cl.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}Codelist":
                        code_list_id = cl.attrib["id"]
                        code_list_name = None
                        code_list_code_id = None
                        code_list_code_name = None
                        for sub_cl in cl:
                            if sub_cl.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common}Name":
                                code_list_name = sub_cl.text
                                continue
                            if sub_cl.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}Code":
                                code_list_code_id = sub_cl.attrib["id"]
                                for sub_cl_name in sub_cl:
                                    code_list_code_name = sub_cl_name.text
                            output.append([code_list_id, code_list_name, code_list_code_id, code_list_code_name])
        code_list_df = pd.DataFrame(data=output,
                                    columns=["CodeListID", "CodeListName", "CodeListCodeID", "CodeListCodeName"]).\
            set_index("CodeListID")
        return code_list_df

    def show_data_flow_list(self):
        """
        Show the list of available data flows in the ECB SDMX database
        :return: a DataFrame with the list of available DSD
        :rtype: pd.DataFrame
        """
        return self.__data_flows

    def retrieve_data(self):
        """
        Call the function to retrieve data from the ECB SDMX database
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
