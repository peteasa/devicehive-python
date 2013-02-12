# -*- coding: utf-8 -*-
# vim:set et tabstop=4 shiftwidth=4 nu nowrap fileencoding=utf-8 encoding=utf-8:

from zope.interface import implements
from twisted.python import log
from twisted.web.client import HTTP11ClientProtocol
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory, Protocol
from devicehive import ApiInfoRequest
from devicehive.interfaces import IProtoFactory, IProtoHandler
from devicehive.utils import TextDataConsumer, JsonDataConsumer, parse_url, parse_date
from devicehive.ws import WebSocketFactory, WS_STATE_WS_CONNECTING
from devicehive.poll import PollFactory


__all__ = ['AutoProtocol', 'AutoFactory']


class AutoProtocol(HTTP11ClientProtocol):
    def __init__(self, factory):
        HTTP11ClientProtocol.__init__(self)
        self.factory = factory
    
    def connectionMade(self) :
        self.request(ApiInfoRequest(self.factory.url, self.factory.host)).addCallbacks(self.api_received, self.api_failed)
    
    def api_received(self, response):
        if response.code == 200 :
            result_proto = Deferred()
            result_proto.addCallbacks(self.api_succeed, self.api_failed)
            response.deliverBody(JsonDataConsumer(result_proto))
        else :
            def get_response_text(reason):
                self.api_failed(reason)
            response_defer = Deferred()
            response_defer.addBoth(get_response_text)
            response.deliverBody(TextDataConsumer(response_defer))
    
    def api_succeed(self, resp):
        self.factory.api_received(resp['webSocketServerUrl'], resp['serverTimestamp'])
    
    def api_failed(self, reason):
        self.factory.api_failed(reason)


class AutoFactory(ClientFactory):
    
    implements(IProtoFactory, IProtoHandler)
    
    url = 'http://localhost'
    host = 'localhost'
    port = 80
    
    ws_url = 'http://localhost'
    ws_host = 'localhost'
    ws_port = 8020
    
    handler = None
    
    def __init__(self, handler):
        self.handler  = handler
        self.handler.factory = self
        self.factory  = None
    
    def buildProtocol(self, addr):
        return AutoProtocol(self)
    
    def clientConnectionFailed(self, connector, reason):
        log.err('Failed to make API info call. Reason: {0}.'.format(reason))
        self.handle_connection_failure(reason)
    
    def api_received(self, wsurl, server_time):
        log.msg('API info called successfully has been made.')
        self.ws_url, self.ws_host, self.ws_port  = parse_url(wsurl.replace('ws://', 'http://', 1).replace('wss://', 'https://'))
        self.server_time = parse_date(server_time)
        self.handler.on_apimeta(wsurl, server_time)
        if (self.ws_url is not None) and len(self.ws_url) > 0 :
            self.connect_ws()
        else :
            self.connect_poll()
    
    def api_failed(self, reason):
        self.connect_poll()
    
    def handle_connection_failure(self, reason):
        if isinstance(self.factory, WebSocketFactory) :
            self.connect_poll()
        else :
            self.handler.on_connection_failed(reason)
    
    def connect_ws(self):
        log.msg('WebSocket protocol has been selected. URL: {0}; HOST: {1}; PORT: {2};'.format(self.ws_url, self.ws_host, self.ws_port))
        factory = WebSocketFactory(self)
        factory.url  = self.ws_url
        factory.host = self.ws_host
        factory.port = self.ws_port
        factory.state = WS_STATE_WS_CONNECTING
        reactor.connectTCP(factory.host, factory.port, factory)
    
    def connect_poll(self):
        log.msg('Long-Polling protocol has been selected.')
        factory = PollFactory(self)
        factory.url = self.url
        factory.host = self.host
        factory.port = self.port
        reactor.connectTCP(self.host, self.port, self.factory)
    
    # begin IProtoHandler implementation
    def on_apimeta(self, websocket_server, server_time):
        self.handler.on_apimeta(websocket_server, server_time)
    
    def on_connected(self):
        self.handler.on_connected()
    
    def on_connection_failed(self, reason):
        log.err('Sub-factory connection failure. Reason: {0}.'.format(reason))
        self.handle_connection_failure(reason)
    
    def on_closing_connection(self):
        self.handler.on_closing_connection()
    
    def on_command(self, device_id, command, finished):
        self.on_command(device_id, command, finished)
    
    def on_failure(self, device_id, reason):
        self.handler.on_failure(device_id, reason)
    # end IProtoHandler implementation
    
    # begin IProtoFactory implementation
    def authenticate(self, device_id, device_key):
        return self.subfactory(device_id, device_key)
    
    def notify(self, notification, params, device_id = None, device_key = None):
        return self.factory.notify(notification, params, device_id, device_key)
    
    def update_command(self, command, device_id = None, device_key = None):
        return self.factory.update_command(command, device_id, device_key)
    
    def subscribe(self, device_id = None, device_key = None):
        return self.factory.subscribe(device_id, device_key)
    
    def unsubscribe(self, device_id = None, device_key = None):
        return self.factory.unsubscribe(device_id, device_key)
    
    def device_save(self, info):
        return self.factory.device_save(info)
    # end IProtoFactory implementation

