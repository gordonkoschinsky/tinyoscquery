import requests
from zeroconf import ServiceInfo

from tinyoscquery.shared.host_info import OSCHostInfo
from tinyoscquery.shared.osc_path_node import OSCPathNode


class OSCQueryClient(object):
    def __init__(self, service_info) -> None:
        if not isinstance(service_info, ServiceInfo):
            raise Exception("service_info isn't a ServiceInfo class!")

        if service_info.type != "_oscjson._tcp.local.":
            raise Exception("service_info does not represent an OSCQuery service!")

        self.service_info = service_info
        self.last_json = None

    def _get_query_root(self) -> str:
        return f"http://{self._get_ip_str()}:{self.service_info.port}"

    def _get_ip_str(self) -> str:
        ip_str = ".".join([str(int(num)) for num in self.service_info.addresses[0]])
        return ip_str

    def query_node(self, node: str = "/") -> OSCPathNode | None:
        url = self._get_query_root() + node
        r = None
        try:
            r = requests.get(url)
        except Exception as ex:
            print("Error querying node...", ex)
        if r is None:
            return None

        if r.status_code == 404:
            return None

        if r.status_code != 200:
            raise Exception("Node query error: (HTTP", r.status_code, ") ", r.content)

        self.last_json = r.json()

        return OSCPathNode.from_json(self.last_json)

    def get_host_info(self) -> OSCHostInfo | None:
        url = self._get_query_root() + "/HOST_INFO"
        r = None
        try:
            r = requests.get(url)
        except Exception:
            # print("Error querying HOST_INFO...", ex)
            pass
        if r is None:
            return None

        if r.status_code != 200:
            raise Exception("Node query error: (HTTP", r.status_code, ") ", r.content)

        json = r.json()
        hi = OSCHostInfo(json["NAME"], json["EXTENSIONS"])
        if "OSC_IP" in json:
            hi.osc_ip = json["OSC_IP"]
        else:
            hi.osc_ip = self._get_ip_str()

        if "OSC_PORT" in json:
            hi.osc_port = json["OSC_PORT"]
        else:
            hi.osc_port = self.service_info.port

        if "OSC_TRANSPORT" in json:
            hi.osc_transport = json["OSC_TRANSPORT"]
        else:
            hi.osc_transport = "UDP"

        return hi
