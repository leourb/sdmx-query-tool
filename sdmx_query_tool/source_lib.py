"""Wrapper module to call all sub modules"""

from .sources.ecb import ECB
from .sources.imf import IMF


class SDMXQueryTool:
    """Tool to query SDMX sources"""

    def __init__(self):
        """Initialize the function with the given inputs"""
        self.__ecb = ECB()
        self.__imf = IMF()

    @staticmethod
    def get_help():
        """
        Provides a brief description of the implemented inputs for each source
        :return: a text with the required inputs and implement modules
        :rtype: dict
        """
        sources = {
            "ECB": "Help page: https://sdw-wsrest.ecb.europa.eu/help/"
        }
        return sources

    def ecb(self):
        """
        Return the ECB class publicly
        :return: the ECB class publicly
        :rtype: ECB
        """
        return self.__ecb

    def imf(self):
        """
        Return the IMF class publicly
        :return: the IMF class publicly
        :rtype: IMF
        """
        return self.__imf
