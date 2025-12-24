import ipaddress
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from ipaddress import IPv4Address, IPv6Address

from zeroconf import ServiceInfo, Zeroconf

from .shared.host_info import OSCHostInfo
from .shared.osc_path_node import OSCPathNode


class OSCQueryService(object):
    """
    A class providing an OSCQuery service. Automatically sets up an oscjson http server and advertises the oscjson server and osc server on zeroconf.

    Attributes:
        server_name: Name of your OSC Service
        http_port: Desired TCP port number for the oscjson HTTP server
        osc_port: Desired UDP port number for the osc server
        osc_ip: IP address of the oscjson server
    """

    def __init__(
        self,
        server_name: str,
        http_port: int,
        osc_port: int,
        osc_ip: IPv4Address | IPv6Address | str = "127.0.0.1",
    ) -> None:
        self.server_name = server_name
        self.http_port = http_port
        self.osc_port = osc_port
        self.osc_ip = ipaddress.ip_address(osc_ip)

        self.root_node = OSCPathNode("/", description="root node")
        self.host_info = OSCHostInfo(
            server_name,
            {
                "ACCESS": True,
                "CLIPMODE": False,
                "RANGE": False,
                "TYPE": True,
                "VALUE": True,
            },
            str(self.osc_ip),
            self.osc_port,
            "UDP",
        )

        self._zeroconf = Zeroconf()
        self._start_osc_query_service()
        self._advertise_osc_service()
        self.http_server = OSCQueryHTTPServer(
            self.root_node, self.host_info, ("", self.http_port), OSCQueryHTTPHandler
        )
        self.http_thread = threading.Thread(target=self._start_http_server)
        self.http_thread.start()

    def __del__(self):
        if hasattr(self, "_zeroconf"):
            self._zeroconf.unregister_all_services()

    def add_node(self, node: OSCPathNode):
        self.root_node.add_child_node(node)

    def _start_osc_query_service(self):
        oscqs_desc = {"txtvers": 1}
        oscqs_info = ServiceInfo(
            "_oscjson._tcp.local.",
            "%s._oscjson._tcp.local." % self.server_name,
            self.http_port,
            0,
            0,
            oscqs_desc,
            "%s.oscjson.local." % self.server_name,
            addresses=["127.0.0.1"],
            # addresses=[self.osc_ip], # TODO: Understand zeroconf and maybe fix this
        )
        self._zeroconf.register_service(oscqs_info)

    def _start_http_server(self):
        self.http_server.serve_forever()

    def _advertise_osc_service(self):
        osc_desc = {"txtvers": 1}
        osc_info = ServiceInfo(
            "_osc._udp.local.",
            "%s._osc._udp.local." % self.server_name,
            self.osc_port,
            0,
            0,
            osc_desc,
            "%s.osc.local." % self.server_name,
            addresses=["127.0.0.1"],
        )

        self._zeroconf.register_service(osc_info)


class OSCQueryHTTPServer(HTTPServer):
    def __init__(
        self,
        root_node,
        host_info,
        server_address: tuple[str, int],
        request_handler_class,
        bind_and_activate: bool = ...,
    ) -> None:
        super().__init__(server_address, request_handler_class, bind_and_activate)
        self.root_node = root_node
        self.host_info = host_info


class OSCQueryHTTPHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if "HOST_INFO" in self.path:
            self.send_response(200)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            self.wfile.write(bytes(str(self.server.host_info.to_json()), "utf-8"))
            return
        node = self.server.root_node.find_subnode(self.path)
        if node is None:
            self.send_response(404)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            self.wfile.write(bytes("OSC Path not found", "utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            self.wfile.write(bytes(str(node.to_json()), "utf-8"))

    def log_message(self, format, *args):
        pass
