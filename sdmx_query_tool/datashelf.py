"""Module to query data through SDMX sources"""

ECB = {
    "endpoint": {
        "protocol": "https://",
        "wsEntryPoint": "sdw-wsrest.ecb.europa.eu/service/",
        "resource": "data/",
        "datastructure": "datastructure/",
        "dataflow": "dataflow/",
        "codelist": "codelist/"
    },
    "inputs": {
        "start_period": "startPeriod={}",
        "end_period": "endPeriod={}",
        "last_n_observations": "lastNObservations={}",
        "first_n_observations": "firstNObservations={}",
        "detail": "detail={}",
        "updated_after": "updatedAfter={}",
        "include_history": "includeHistory={}"
    }
}

IMF = {
    "data_flow_list": "https://registry.sdmx.org/ws/public/sdmxapi/rest/dataflow/"
}

OECD = {
    "data_flow_list": "https://stats.oecd.org/restsdmx/sdmx.ashx/GetDataStructure/ALL",
    "data": "http://stats.oecd.org/restsdmx/sdmx.ashx/GetData/",
    "code_list": "http://stats.oecd.org/restsdmx/sdmx.ashx/GetSchema/",
    "inputs": {
        "start_period": "startPeriod={}",
        "end_period": "endPeriod={}"
    }
}

INSEE = {
    "data_flow_list": "https://bdm.insee.fr/series/sdmx/dataflow/FR1",
    "data": "https://bdm.insee.fr/series/sdmx/data/{}",
    "code_list": "https://bdm.insee.fr/series/sdmx/codelist/",
    "code_list_data_flow": "https://bdm.insee.fr/series/sdmx/datastructure/FR1/{}",
    "inputs": {
        "start_period": "startPeriod={}",
        "end_period": "endPeriod={}",
        "last_n_observations": "lastNObservations={}",
        "first_n_observations": "firstNObservations={}",
        "updated_after": "updatedAfter={}",
        "include_history": "includeHistory={}"
    }
}


class DataShelf:
    """Container for static data"""

    def __init__(self):
        """Initialize the class"""
        self.__ecb = ECB
        self.__imf = IMF
        self.__oecd = OECD
        self.__insee = INSEE

    def ecb(self):
        """
        Return the ECB dictionary publicly
        :return: a dictionary with the ECB configuration
        :rtype: dict
        """
        return self.__ecb

    def imf(self):
        """
        Return the IMF dictionary publicly
        :return: a dictionary with the IMF configuration
        :rtype: dict
        """
        return self.__imf

    def oecd(self):
        """
        Return the OECD dictionary publicly
        :return: a dictionary with the OECD configuration
        :rtype: dict
        """
        return self.__oecd

    def insee(self):
        """
        Return the INSEE dictionary publicly
        :return: a dictionary with the INSEE configuration
        :rtype: dict
        """
        return self.__insee
