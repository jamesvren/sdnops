import os
from rest import RestAPI, Resource
from util import logger

log = logger(__name__)

class SdnApi(RestAPI):
    def __init__(self, vip=None, port=None):
        vip = vip if vip else os.environ.get('INT_VIP', '0.0.0.0')
        port = port if port else os.environ.get('AUTH_PORT', 5000)
        super().__init__(auth_host=vip, auth_port=port, host=vip, port=8082)

    def get_vrouters(self):
        node = Resource(res_type='node')
        status, nodes = self.req('post', self.encode_url('/neutron/node'), node.body)
        if status != 200:
            log.error(f'Lost connection to SDN API {self.auth_host}, auth port {self.auth_port}. Status: {status}, {nodes}')
            return []
        return nodes['virtual_routers']
