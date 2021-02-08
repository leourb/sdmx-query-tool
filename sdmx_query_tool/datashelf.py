"""Module to query data through SDMX sources"""

ECB = {
    "endpoint": {
        "protocol": "https://",
        "wsEntryPoint": "sdw-wsrest.ecb.europa.eu/service/",
        "resource": "data/",
        "datastructure": "datastructure/"
    },
    "inputs": {
        "start_period": "startPeriod={}",
        "end_period": "end_period={}",
        "last_n_observations": "lastNObservations={}",
        "first_n_observations": "firstNObservations={}",
        "detail": "detail={}",
        "updated_after": "updatedAfter={}",
        "include_history": "includeHistory={}"
    }
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
