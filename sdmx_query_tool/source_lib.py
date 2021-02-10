"""Wrapper module to call all sub modules"""

from .sources.ecb import ECB
from .sources.imf import IMF
from .sources.insee import INSEE
from .sources.oecd import OECD


class SDMXQueryTool:
    """Tool to query SDMX sources"""

    def __init__(self):
        """Initialize the function with the given inputs"""
        self.__ecb = ECB
        self.__imf = IMF
        self.__oecd = OECD
        self.__insee = INSEE

    @staticmethod
    def get_help():
        """
        Provides a brief description of the implemented inputs for each source
        :return: a text with the required inputs and implement modules
        :rtype: dict
        """
        sources = {
            "ECB": "Help page: https://sdw-wsrest.ecb.europa.eu/help/",
            "IMF": "Help page: https://sdmxcentral.imf.org/overview.html#",
            "OECD": "Help page: https://data.oecd.org/api/sdmx-ml-documentation/",
            "INSEE": "Help page: https://www.insee.fr/en/information/2868055"
        }
        return sources

    def ecb(self):
        """
        Return the ECB class publicly
        :return: the ECB class publicly
        :rtype: ECB
        """
        return self.__ecb()

    def imf(self):
        """
        Return the IMF class publicly
        :return: the IMF class publicly
        :rtype: IMF
        """
        return self.__imf()

    def oecd(self):
        """
        Return the OECD class publicly
        :return: the OECD class publicly
        :rtype: OECD
        """
        return self.__oecd()

    def insee(self):
        """
        Return the INSEE class publicly
        :return: the INSEE class publicly
        :rtype: INSEE
        """
        return self.__insee()
