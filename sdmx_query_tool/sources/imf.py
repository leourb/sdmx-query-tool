"""Module to query SDMX data from the IMF"""

from ..datashelf import DataShelf


class IMF:
    """Class to interface with the IMF"""

    def __init__(self):
        """Initialize the class"""
        self.__datashelf = DataShelf().imf()
        self.__dsd = self.__refresh_dsd_list()

    def __refresh_dsd_list(self):
        """
        Refresh the list of the data flows
        :return: a DataFrame with the list of the available data flows
        """