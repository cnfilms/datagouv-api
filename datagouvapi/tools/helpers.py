import unicodedata


class GouvApiException(Exception):

    def __init__(self, service, message, status_code):
        self.service = str(service)
        self.message = message
        self.status_code = status_code

    def __str__(self):
        status = f" - status code {self.status_code}" if self.status_code is not None else ""
        return repr(f"GOUV API error on {self.service}{status} : {self.message}")

def unaccent(string):
    """Removes accents from a string"""
    text = unicodedata.normalize('NFKD', string).encode('ascii', 'ignore')
    return str(text.decode('utf-8'))


class GouvApiWarning:
    def __init__(self, identifier, message):
        self.identifier = identifier
        self.message = message

    def __str__(self):
        return repr(f"{self.message} for result id: {self.identifier}")
