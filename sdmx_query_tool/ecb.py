"""Module to interface with the ECB SDMX portal"""

import requests
import xml.etree.ElementTree as eT

from io import BytesIO

import pandas as pd

from .datashelf import DataShelf


class ECB:
    """Class containing the SDMX instructions for the ECB"""

    def __init__(self):
        """Initialize the class"""
        self.__datashelf = DataShelf().ecb()

    @staticmethod
    def show_dsd():
        """
        Show the list of DSDs maintained by the ECB
        :return: a DataFrame with the list of DSDs
        :rtype: pd.DataFrame
        """
        url = f"{ECB().__datashelf['protocol']}{ECB().__datashelf['wsEntryPoint']}" \
              f"{ECB().__datashelf['datastructure']}ECB?references=dataflow"
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
