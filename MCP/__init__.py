import requests
import logging

logger = logging.getLogger(__name__)

class MCPToolDiscovery:
    """Discovers tools from MCP-compliant services."""
    def __init__(self, services_config):
        self.services = services_config

    async def discover_tools(self, service_key: str):
        """Fetch tools from a specific service's /mcp/tools endpoint."""
        if service_key not in self.services:
            raise ValueError(f"Service '{service_key}' not found in configuration.")
        
        service = self.services[service_key]
        tools_endpoint = service['endpoints'].get('tools')
        if not tools_endpoint:
            logger.warning(f"No 'tools' endpoint for service '{service_key}'.")
            return {'tools': []}

        url = f"{service['baseUrl']}{tools_endpoint}"
        logger.info(f"Discovering tools for '{service_key}' from {url}")

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            tools_data = response.json()
            
            # Cache the discovered tools
            self.services[service_key]['tools_cache'] = tools_data
            self.services[service_key]['last_discovery'] = logger.info(f"Discovered {len(tools_data.get('tools', []))} tools for {service_key}")
            return tools_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to discover tools for '{service_key}': {e}")
            return {'tools': []}

    def get_available_tools(self, service_key: str):
        """Get available tools from the cache."""
        if service_key not in self.services:
            return []
        return self.services[service_key].get('tools_cache', {}).get('tools', [])
