"""Module to query data through SDMX sources"""

ECB = {
    "protocol": "https://",
    "wsEntryPoint": "sdw-wsrest.ecb.europa.eu/service/",
    "resource": "data/",
    "datastructure": "datastructure/"
}


class DataShelf:
    """Container for static data"""

    def __init__(self):
        """Initialize the class"""
        self.__ecb = ECB

    def ecb(self):
        """
        Return the ECB dictionary publicly
        :return: a dictionary with the static ECB information
        :rtype: dict
        """
        return self.__ecb
