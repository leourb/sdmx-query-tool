"""Wrapper module to call all sub modules"""

from .sources.ecb import ECB
from .sources.imf import IMF
from .sources.insee import INSEE
from .sources.oecd import OECD


class SDMXQueryTool:
    """Tool to query SDMX sources"""

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

    @staticmethod
    def ecb():
        """
        Return the ECB class publicly
        :return: the ECB class publicly
        :rtype: ECB
        """
        return ECB()

    @staticmethod
    def imf():
        """
        Return the IMF class publicly
        :return: the IMF class publicly
        :rtype: IMF
        """
        return IMF()

    @staticmethod
    def oecd():
        """
        Return the OECD class publicly
        :return: the OECD class publicly
        :rtype: OECD
        """
        return OECD()

    @staticmethod
    def insee():
        """
        Return the INSEE class publicly
        :return: the INSEE class publicly
        :rtype: INSEE
        """
        return INSEE()
