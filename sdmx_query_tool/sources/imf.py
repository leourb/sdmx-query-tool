"""Module to query SDMX data from the IMF"""

import requests
import xml.etree.ElementTree as eT

from io import BytesIO

import pandas as pd

from ..datashelf import DataShelf


class IMF:
    """Class to interface with the IMF"""

    def __init__(self):
        """Initialize the class"""
        self.__data_shelf = DataShelf().imf()
        self.__data_flows = self.__refresh_data_flow_list()

    def __refresh_data_flow_list(self):
        """
        Refresh the list of the data flows
        :return: a DataFrame with the list of the available data flows
        """
        url = self.__data_shelf['data_flow_list']
        imf_data_flows = requests.get(url).content
        output = list()
        for _, element in eT.iterparse(BytesIO(imf_data_flows)):
            if element.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}Dataflows":
                for data_flow in element:
                    if data_flow.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}Dataflow":
                        agency_id = data_flow.attrib["agencyID"]
                        data_flow_id = data_flow.attrib["id"]
                        data_flow_name = None
                        for detailed_info in data_flow:
                            if detailed_info.tag == "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common}Name":
                                data_flow_name = detailed_info.text
                                continue
                        output.append([agency_id, data_flow_id, data_flow_name])
        print(Warning(f"Data may be truncated. Please visit {'https://sdmxcentral.imf.org/data/overview.html'} for a "
                      f"full list of Data Flows available to be queried."))
        results = pd.DataFrame(data=output, columns=["AgencyID", "DataFlowID", "DataFlowName"]).set_index("AgencyID")
        return results

    def show_data_flows(self):
        """
        Show Data Flows publicly
        :return: a DataFrame with the list of the Data Flows
        :rtype: pd.DataFrame
        """
        return self.__data_flows
