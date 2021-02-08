"""Wrapper module to call all sub modules"""

from .ecb import ECB


class SDMXQueryTool:
    """Tool to query SDMX sources"""

    def __init__(self):
        """Initialize the function with the given inputs"""
        self.__ecb = ECB()

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

