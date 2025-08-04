#!/usr/bin/env python 

import os 
import json
import asyncio
import threading
import subprocess
import websockets
import netifaces

import time 
import logging
logger = logging.getLogger(__name__)

def bash_run_d(command_args): 
    logger.info(f"{command_args=}")
    result = subprocess.run(command_args) 
    logger.debug(f"returncode: {result.returncode }")
    return result.returncode 

def bash_run(command_args): 
    logger.info(f"{command_args=}")
    result = subprocess.run(command_args, capture_output=True, text=True) 
    logger.debug(f"stdout---\n{result.stdout}")
    logger.debug(f"stderr--\n{result.stderr}") 
    logger.debug(f"returncode: {result.returncode }")
    return result.returncode 

def check_network_addr(interface): 
    logger.info("Check interface addresses")
    addresses = netifaces.ifaddresses(interface)
    logger.debug(f"stdout---\n{addresses}")
    if netifaces.AF_INET in addresses:
        ipv4_addresses = addresses[netifaces.AF_INET]
        if len(ipv4_addresses) > 0: 
            return ipv4_addresses[0]

def find_key_value(filename, key): 
    with open(filename) as f:
        for line in f: 
            logger.debug(line)
            parts = line.split("=") 
            if len(parts) > 1 and key == parts[0].strip(): 
                value = parts[1].strip().strip('\"') 
                return value  

def check_wifi_sta_id(): 
    wpa_conf = "/etc/wpa_supplicant/wpa_supplicant.conf"
    logger.info(f"Check wifi ssid and password from {wpa_conf}")
    ssid = find_key_value(wpa_conf, "ssid") 
    password = find_key_value(wpa_conf, "psk") 
    return ssid, password 

def check_wifi_ap_id(): 
    apd_conf = "/etc/hostapd/hostapd.conf"
    logger.info(f"Check wifi ssid and password from {apd_conf}")
    ssid = find_key_value(apd_conf, "ssid") 
    password = find_key_value(apd_conf, "wpa_passphrase") 
    return ssid, password 

# handle requests from websocket connection 
# JSON-RPC 2.0 protocol 
class WebsocketConnection(object): 
    def __init__(self, websocket): 
        self._websocket = websocket 

        # supported reqeusts 
        self._handlers = {
            "check_system_status": self.check_system_status, 
            "restart_system": self.restart_system, 
            "shutdown_system": self.shutdown_system, 
            "check_software_versions": self.check_software_versions, 
            "install_software": self.install_software, 
            "check_wifi_ap_status": self.check_wifi_ap_status, 
            "setup_wifi_ap": self.setup_wifi_ap, 
            "check_wifi_sta_status": self.check_wifi_sta_status, 
            "setup_wifi_sta": self.setup_wifi_sta, 
        } 

        # paths 
        self.service_dir = os.path.dirname(os.path.abspath(__file__)) 
        self.software_dir = os.path.dirname(self.service_dir) 
        self.network_dir = os.path.join(self.software_dir, "network") 
        self.system_dir = os.path.join(self.software_dir, "system") 
        self.updates_dir = os.path.join(self.software_dir, "updates") 
        logger.info(f"{self.service_dir=}")
        logger.info(f"{self.software_dir=}") 
        logger.info(f"{self.network_dir=}") 
        logger.info(f"{self.system_dir=}") 
        logger.info(f"{self.updates_dir=}") 

    # send a message to client 
    async def send_response(self, response): 
        logger.info(f"Send response: {response}")
        message = json.dumps(response)  
        await self._websocket.send(message)

    # status message 
    async def send_status_response(self, code = -1, message = "", id = None): 
        logger.info("Send status response...")
        await self.send_response({ "error": { "code": code, "message": message}, "id": id }) 

    # result message 
    async def send_result_response(self, result = None, id = None): 
        logger.info("Send result response...")
        await self.send_response({ "result": result, "id": id }) 

    # handle requests until the connection is closed  
    async def handle_requests(self): 
        try: 
            async for message in self._websocket: 
                try: 
                    request = json.loads(message) 
                    logger.info(f"Request received: {request}")
                    await self.handle_request(request)
                except websockets.exceptions.ConnectionClosed: 
                    raise 
                except Exception as e: 
                    logger.warning(f"Error while handling request: {e}")
        except websockets.exceptions.ConnectionClosed:
            raise 
        except Exception as e: 
            logger.error(f"Error while handling requests: {e}")

    async def handle_request(self, request): 
        assert(isinstance(request, dict))
        method = request["method"] if "method" in request else None 
        params = request["params"] if "params" in request else None 
        id = request["id"] if "id" in request else None 
        logger.debug(f"{method=}")
        logger.debug(f"{params=}") 
        logger.debug(f"{id=}") 
        if method in self._handlers: 
            await self._handlers[method](params=params, id=id) 
        else: 
            logger.warning(f"Method not in list: {self._handlers.keys()}") 
            await self.send_status_response(-1, "Unsupported method", id)

    async def check_system_status(self, params = None, id = None): 
        logger.info("check_system_status") 
        await self.send_status_response(-1, "Not implemented", id) 

    async def restart_system(self, params = None, id = None): 
        logger.warning("restart_system")
        try: 
            code = bash_run_d(["sudo", "-b", "bash", "-c", "sleep 5; reboot"]) 
            if code == 0: 
                await self.send_status_response(-1, "System restart, please reconnect later", id) 
            else: 
                 await self.send_status_response(code, "Failed to restart the system", id) 
        except Exception as e: 
            logger.warning(f"Error to restart the system: {e}") 
            await self.send_status_response(-1, "Error to restart the system", id)

    async def shutdown_system(self, params = None, id = None): 
        logger.warning("shutdown_system")
        try: 
            code = bash_run_d(["sudo", "-b", "bash", "-c", "sleep 5; shutdown now"])  
            if code == 0: 
                await self.send_status_response(-1, "System shutdown in seconds", id) 
            else: 
                 await self.send_status_response(code, "Failed to shutdown the system", id) 
        except Exception as e: 
            logger.warning(f"Error to shutdown the system: {e}") 
            await self.send_status_response(-1, "Error to shutdown the system", id)
   
    async def check_software_versions(self, params = None, id = None): 
        logger.info("check_software_versions")
        try: 
            code = bash_run([os.path.join(self.system_dir, "updates.sh"), "check"])
            if code == 0: 
                logger.info("Software updates checked successfully")
                await self.send_status_response(0, "Software updates checked successfully", id)
            else: 
                logger.warning("Failed to check software updates")
                await self.send_status_response(code, "Failed to check software updates", id)
        except Exception as e: 
            logger.warning(f"Error to check software updates: {e}") 
            await self.send_status_response(-1, "Error to check software updates", id) 

        installed_version = None 
        try: 
            version_file = os.path.join(self.software_dir, "VERSION.txt")
            logger.info(f"Check installed version from {version_file}")
            with open(version_file) as f: 
                for line in f: 
                    logger.debug(f"{line=}")
                    key, value = line.split("=") 
                    if key == "CURRENT_VERSION": 
                        installed_version = value.strip()
                        break 
        except Exception as e: 
            logger.warning(f"Error check installed version: {e}")
            await self.send_status_response(-1, "Error to check installed version", id)
        logger.info(f"{installed_version=}")

        latest_version = None 
        fallback_version = None 
        try: 
            version_file = os.path.join(self.updates_dir, "VERSION.txt")
            logger.info(f"Check latest and fallback version from {version_file}")
            with open(version_file) as f: 
                for line in f: 
                    logger.debug(f"{line=}")
                    key, value = line.split("=") 
                    if key == "CURRENT_VERSION": 
                        latest_version = value.strip() 
                    elif key == "FALLBACK_VERSION": 
                        fallback_version = value.strip() 
        except Exception as e: 
            logger.warning(f"Error to check updated versions: {e}")
            await self.send_status_response(-1, "Error to check updated versions", id)    
        logger.info(f"{latest_version=}")
        logger.info(f"{fallback_version=}")

        result = {
            "installed_version": installed_version, 
            "latest_version": latest_version, 
            "fallback_version": fallback_version,
        }
        await self.send_result_response(result, id) 
    
    async def install_software(self, params = None, id = None): 
        logger.info("install_software")
        version = params["version"] if "version" in params else None 
        logger.info(f"{version=}")
        if version:
            try: 
                logger.info(f"install software {version}") 
                await self.send_status_response(0, "Installation takes time, please wait...", id) 
                code = bash_run([os.path.join(self.system_dir, "updates.sh"), "install", version]) 
                if code == 0: 
                    await self.send_status_response(code, f"Software {version} installed successfully", id) 
                    await self.restart_system(id = id)
                else: 
                    await self.send_status_response(code, f"Failed to install software {version}", id) 
            except Exception as e: 
                logger.warning(f"Error to install software: {e}") 
                await self.send_status_response(-1, f"Error to install software {version}", id) 
        else: 
            await self.send_status_response(-1, "Software version is not set", id)

    async def check_wifi_ap_status(self, params = None, id = None): 
        logger.info("check_wifi_ap_status")
        try: 
            ssid, password = check_wifi_ap_id() 
            logger.info(f"{ssid=}") 
            logger.info(f"{password=}")
            if ssid is None: 
                await self.send_status_response(0, "WiFi AP is not setup", id) 
        except Exception as e: 
            logger.warning(f"Error checking wifi ap: {e}")
            await self.send_status_response(-1, "Error to check WiFi AP", id)  
            
        try: 
            address = check_network_addr("uap0")
            logger.info(f"uap0: {address}")
            if address is None: 
                await self.send_status_response(-1, "WiFi is not activated" , id) 
        except Exception as e: 
            logger.waning(f"Error to check wifi IP address: {e}") 
            await self.send_status_response(-1, "Error to check IP address", id)
            
        result = {
            "setup": { "ssid": ssid, "password": password }, 
            "address": address
        }
        await self.send_result_response(result, id)

    async def setup_wifi_ap(self, params = None, id = None): 
        logger.info(f"setup_wifi_ap: {params}") 
        await self.send_status_response(-1, "Not implemented", id)

    async def check_wifi_sta_status(self, params = None, id = None): 
        logger.info("check_wifi_sta_status")
        try: 
            ssid, password = check_wifi_sta_id() 
            logger.info(f"{ssid=}")
            logger.info(f"{password=}")
            if ssid is None: 
                await self.send_status_response(0, "WiFi STA is not setup", id) 
        except Exception as e: 
            logger.warning(f"Error to check wifi sta: {e}")
            await self.send_status_response(-1, "Error to check WiFi STA", id)  
        
        try: 
            address = check_network_addr("wlan0")
            logger.info(f"wlan0: {address}")
            if address is None: 
                await self.send_status_response(-1, "WiFi is not connected" , id)
        except Exception as e: 
            logger.waning(f"Error to check IP address: {e}") 
            await self.send_status_response(-1, "Error to check IP address", id)
            
        result = {
            "setup": { "ssid": ssid, "password": password }, 
            "address": address
        }
        await self.send_result_response(result, id)

    async def setup_wifi_sta(self, params = None, id = None): 
        logger.info(f"setup_wifi_sta: {params}") 
        if "ssid" in params: 
            ssid = params["ssid"] 
            password = params["password"] if "password" in params else None 
            try: 
                logger.info("check wifi settings")
                current_ssid, current_password = check_wifi_sta_id() 
                logger.info(f"{current_ssid=}") 
                logger.info(f"{current_password=}")
            except Exception as e: 
                logger.waning(f"Error to check wifi settings: {e}")

            if ssid == current_ssid and password == current_password: 
                await self.send_status_response(-1, "WiFi settings has no change", id)
            else: 
                try: 
                    code = bash_run([os.path.join(self.network_dir, "setup-wifi-sta.sh"), ssid, password])
                    if code == 0: 
                        await self.send_status_response(code, "WiFi settings changed", id) 
                        try: 
                            logger.info("restart network") 
                            script = os.path.join(self.network_dir, "restart-wifi.sh")
                            code = bash_run_d(["sudo", "-b", "bash", "-c", f"sleep 5; bash {script}"])
                            if code == 0: 
                                await self.send_status_response(-1, "Network restart, please reconnect later", id)
                            else: 
                                await self.send_status_response(code, "Failed to restart network", id)
                        except Exception as e: 
                            await self.send_status_response(-1, "Error to restart network", id)
                    else: 
                        await self.send_status_response(code, "Failed to change WiFi settings", id) 
                except Exception as e: 
                    logger.warning(f"Error to change wifi settings: {e}") 
                    await self.send_status_response(-1, "Error to change WiFi settings", id) 
        else: 
            await self.send_status_response(-1, "WiFi SSID is not set", id) 

class WebsocketServer(object): 
    def __init__(self, port = 8090): 
        self.port = port 
        self._connections = set() 
        self._server = None
        self._stop_event = None  
        self._loop = None 
        self._thread = None 

    # handle client connection
    async def handler(self, websocket):
        logger.info(f"Websocket connection from {websocket.remote_address[0]}") 
        connection = WebsocketConnection(websocket)
        self._connections.add(connection)
        try:
            await connection.handle_requests() 
            await websocket.wait_closed()
        except websockets.exceptions.ConnectionClosed as e: 
            logger.warning(e)
        except Exception as e: 
            logger.warning(e)
        finally: 
            logger.error(f"Remove websocket connection from {websocket.remote_address[0]}")
            self._connections.remove(connection)
            
    def run_forever(self):
        async def _run(): 
            logger.info(f"Run webocket server at port {self.port}") 
            self._loop = asyncio.get_running_loop() 
            self._stop_event = asyncio.Event() 
            self._server = await websockets.serve(self.handler, "0.0.0.0", self.port)
            await self._stop_event.wait()
            await self._server.wait_closed() 
        asyncio.run(_run())

    def start(self): 
        if self._thread is None: 
            logger.info(f"Start webocket server") 
            self._thread = threading.Thread(target=self.run_forever)
            self._thread.start()
    
    def stop(self): 
        if self._thread is not None: 
            logger.warning("Stop websocket server...")
            self._loop.call_soon_threadsafe(self._stop_event.set)
            self._loop.call_soon_threadsafe(self._server.close)
            self._thread.join()
            self._thread = None 
            self._connections.clear() 
            logger.warning("Websocket server stopped")

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler 
class WebServer(object): 
    class HttpRequestHandler(SimpleHTTPRequestHandler): 
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs, directory="web-ui")
    
        def do_GET(self):
            logger.info(f"HTTP request for {self.path}")
            if self.path == "/": 
                self.path = "/net-admin.html" 
            elif not self.path.endswith(".html"): 
                html_path = self.path + ".html" 
                if os.path.exists(self.translate_path(html_path)):
                    self.path = html_path 
            return super().do_GET()

    def __init__(self, port = 8080): 
        self._port = port 
        self._httpd = ThreadingHTTPServer(("", self._port), self.HttpRequestHandler) 
        self._thread = None 

    @property 
    def port(self): 
        return self._port  

    def start(self): 
        if self._thread is None: 
            logger.info(f"Start web server at port {self.port}") 
            self._thread = threading.Thread(target=self._httpd.serve_forever)
            self._thread.start()

    def stop(self): 
        if self._thread is not None: 
            logger.warning("Stop web server...")
            self._httpd.shutdown()
            self._thread.join()
            self._thread = None 
            logger.warning("Web server stopped")

import signal 
def handle_signal(signum, frame):
    logger.warning("Kill signal received")

def run_service(config_file = None): 
    # default config 
    config = {
        "ws_port": 8090, 
        "http_port": 8080, 
    }
    logger.info(f"Default config: {config}")

    # overwrite with config file 
    if config_file: 
        logger.info(f"Load config from {config_file}")
        with open(config_file) as f: 
            config.update(json.load(f))
            logger.info(f"Updated config: {config}")

    # run websocket server 
    ws_port = config["ws_port"] 
    logger.info(f"{ws_port=}")
    ws_server = WebsocketServer(ws_port)
    ws_server.start() 

    # run web server 
    http_port = config["http_port"]
    logger.info(f"{http_port=}") 
    web_server = WebServer(http_port)
    web_server.start() 

    try: 
        logger.warning("Waiting for kill signal...")
        signal.signal(signal.SIGINT, handle_signal) 
        signal.pause() 
    except Exception as e:
        logger.error(f"Error in waiting: {e}")
    finally: 
        web_server.stop() 
        ws_server.stop() 

import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Network Admin Service")
    parser.add_argument("--config_file", "-c", type=str, default="net-admin.json")
    parser.add_argument("--log_level", type=str, default="DEBUG")

    # parser.print_help()
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.info(vars(args))

    # start net-admin server with config file   
    run_service(args.config_file)
