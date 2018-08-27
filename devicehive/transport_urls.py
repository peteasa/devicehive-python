


class TransportUrls(object):
    """Holds url for devicehive server"""

    def __init__(self):
        self.urls = dict()
        self.transport_name = None

    def update(self, k, url):
        transport_name = None
        if url[0:4] == 'http':
            transport_name = 'http'
            if not url.endswith('/'):
                url += '/'
        if url[0:2] == 'ws':
            transport_name = 'websocket'
        if not self.transport_name:
            self.transport_name = transport_name
        assert(self.transport_name == transport_name)

        self.urls[k] = (transport_name,url)

    def getUrl(self, relative_url):
        k = self._decodeRelUrl(relative_url)
        (t,url) = self.urls[k]
        return url

    def getTransportName(self, k):
        if not k in self.urls:
            self.urls[k] = (None,u'')
        (transport_name,u) = self.urls[k]
        return transport_name

    def _decodeRelUrl(self, relative_url):
        # devicehive now split into several servers
        parts = relative_url.split(u'/')
        k = 'frontend_url'
        if "token" in parts[0]:
            k = 'auth_url'
        if "plugin" in parts[0]:
            k = 'plugin_url'
        return k
