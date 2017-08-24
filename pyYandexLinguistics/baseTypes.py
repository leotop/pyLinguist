import requests

from . import logger


class YaTranslateException(Exception):
    """
        Class for possible exceptions during Yandex API usage
    """
    error_codes = {
        400: "Wrong parameter was specified",
        401: "Invalid API key",
        402: "Blocked API key",
        403: "Exceeded the daily limit on the amount of requests",
        404: "Exceeded the daily limit on the amount of translated text",
        413: "Exceeded the maximum text size",
        422: "The text cannot be translated",
        501: "The specified translation direction is not supported",
        503: "Server not available",
    }

    def __init__(self, status_code: int, *args, **kwargs):
        """
        :param status_code: :type int, code, returned from request to API

        >>> YaTranslateException()
        Traceback (most recent call last):
            ...
        TypeError: __init__() missing 1 required positional argument: 'status_code'
        >>> YaTranslateException(400)
        YaTranslateException('Wrong parameter was specified', 400)
        >>> YaTranslateException(300)
        YaTranslateException('Unknown code', 300)
        >>> isinstance(YaTranslateException(400).error_codes, dict)
        True
        """
        message = self.error_codes.get(status_code, "Unknown code")
        super(YaTranslateException, self).__init__(message, status_code,
                                                   *args, **kwargs)


class _YaAPIHandler:
    """
        Generic class for Yandex APIs
    """
    _base_url = r""  # base api url for all requests
    _endpoints = {
        'langs': "getLangs"
    }

    def __init__(self, api_key: str, xml: bool=False):
        """
        :param api_key: :type str, personal API access key, given by Yandex
        :param xml: :type bool, specify returned data format

        >>> _YaAPIHandler()
        Traceback (most recent call last):
            ...
        TypeError: __init__() missing 1 required positional argument: 'api_key'
        >>> _YaAPIHandler('')
        Traceback (most recent call last):
            ...
        YaTranslateException: ('Invalid API key', 401)
        >>> _YaAPIHandler("123")._api_key == "123"
        True
        >>> _YaAPIHandler("123")._json == ".json"
        True
        >>> not _YaAPIHandler("123")._url
        True
        """
        if not api_key:
            raise YaTranslateException(401)
        self._api_key = api_key
        self._json = ".json" if not xml else ""
        self._cache = None
        self._url = self._base_url

    def _make_url(self, endpoint: str, url: str=None) -> str:
        """
        Creates full (base url + endpoint) url for API requests.

        :param endpoint: :type str, one of the keys from self._endpoints dict
        :return: :type str, created url for requests

        >>> not _YaAPIHandler("123")._make_url('')
        True
        >>> _YaAPIHandler("123")._make_url('', "http://url.../") == "http://url.../"
        True
        """
        # not format string for Python less then 3.6 compatibility
        if url:
            return url + self._endpoints.get(endpoint, '')
        return self._url + self._endpoints.get(endpoint, '')

    def _form_params(self, **params) -> dict:
        """
        Returns dict of params for request, including API key and additional params.

        :param callback: name of callback function for JSONB response
        :param kwargs: :type dict, dict of named params
        :return: :type dict, formed params for future requests

        >>> _YaAPIHandler("123")._form_params()
        {'key': '123'}
        >>> 'ui' in _YaAPIHandler("123")._form_params(ui='en')
        True
        >>> 'callback' in _YaAPIHandler("123")._form_params(abs)
        True
        >>> 'callback' not in _YaAPIHandler("123", xml=True)._form_params(abs)
        True
        """
        parameters = {param: params[param] for param in params}
        parameters['key'] = self._api_key
        # for JSONB response
        if 'callback' in parameters and not self._json:
            del parameters['callback']
        return parameters

    def _get_langs(self, url: str, update=False, **parameters) -> dict or list:
        """
        Wrapper for all getLangs API methods.
        Use caching to store received info.

        :param update: :type bool=False, update caching values
        :param parameters: supported additional params: callback, proxies, ui
        :return: :type dict or list
        """
        if update or not self._cache:
            params = self._form_params(**parameters)
            self._cache = self._make_request(
                self._make_url("langs", url),
                post=False,
                **params
            )
        return self._cache

    @staticmethod
    def _make_request(url: str, post: bool=False, **params) -> dict:
        """
        Implements request to API with given params and return content in JSON.

        :param url: :type str, prepared url for request to API
        :param post: :type bool, key for making POST request instead GET
        :param params: additional params for request, transmitted throw 'params' argument
        :return: :type dict, response content in JSON (response.json())
        :exception YaTranslateException, ConnectionError from requests.exceptions
        """
        if post:
            response = requests.post(url, params=params)
        else:
            response = requests.get(url, params=params)
        if not response.ok:
            raise YaTranslateException(response.status_code)
        if 'callback' in params:
            return response
        return response.json()

    def _ok(self, url: str, **params) -> bool:
        """
        To check that the API key is correct.

        :return: :type bool
        """
        try:
            __ = self._get_langs(url, update=True, **params)
        except BaseException as err:
            logger.warning(err)
            return False
        return True


__all__ = ["YaTranslateException"]


if __name__ == "__main__":
    import doctest
    doctest.testmod()
