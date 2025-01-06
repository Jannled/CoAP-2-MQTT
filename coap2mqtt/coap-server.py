import os
from typing import Optional
import argparse
import asyncio
import datetime
import logging

import aiocoap
import aiocoap.resource as resource
import paho.mqtt.client as mqtt
from aiocoap import Code, Message
from aiocoap.numbers.contentformat import ContentFormat
from paho.mqtt.enums import CallbackAPIVersion

from importlib.metadata import version
from urllib.parse import urlparse

# logging setup
logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)


class MQTT_Relay(resource.Resource):
    # MQTT Singleton
    mqtt_client = mqtt.Client(
        #client_id="", userdata=None, protocol=mqtt.MQTTv5#,
        #callback_api_version=CallbackAPIVersion.VERSION2
    )


    @staticmethod
    def onConnect(client, userdata, flags, rc):
        if rc==0:
            logging.info("Connected to MQTT Broker")
        else:
            logging.warning(f"Connection to MQTT failed with code {rc}")

    @staticmethod
    def onDisconnect(client, userdata, reason_code, properties):
        logging.warning(f"Lost connection to MQTT Server: {reason_code}")

    @staticmethod
    def connect_mqtt(
        broker: str, port: int = 1833, 
        keepalive: int = 60, 
        username: Optional[str] = None, 
        password: Optional[str] = None
    ):
        logging.info(f'Connecting to MQTT Server: "{broker}"')

        try:
            MQTT_Relay.mqtt_client.username_pw_set(username, password=password)
            MQTT_Relay.mqtt_client.connect(broker, port, keepalive)
            MQTT_Relay.mqtt_client.on_connect = MQTT_Relay.onConnect
            MQTT_Relay.mqtt_client.on_disconnect = MQTT_Relay.onDisconnect
            MQTT_Relay.mqtt_client.loop_start()
            MQTT_Relay.mqtt_client.subscribe("test/topic")
        except ConnectionRefusedError as e:
            logging.error(f'Connection to MQTT failed: "{e}"')
        except Exception as e:
            logging.error(f'Exception in MQTT lib: "{e}"')


    async def render(self, request: Message):
        topic = "default"
        try:
            requestUri = urlparse(request.get_request_uri())
            topic = str(requestUri.path).removeprefix('/')

            # Drop some topics that seem unreasonable
            if topic == None or len(topic) < 1 or topic in ['/', '()', '#', '$']:
                topic = "default"
        except:
            logging.error("Unable to get request uri")

        # Log or process the request        
        logging.info(f"Received request: {request.code} on {request.get_request_uri()}")
        logging.info(f"Payload: {request.payload.decode('utf-8')}")

        # Publish to MQTT Broker
        try:            
            MQTT_Relay.mqtt_client.publish(
                topic=topic, 
                payload=request.payload.decode(encoding='utf-8')
            )
        except Exception as e:
            logging.error(f'Failed to publish topic {topic}: "{e}"')

        # Respond with a generic message
        return Message(
            code=Code.CONTENT,
            payload=b"Generic response for any resource"
        )


class Welcome(resource.Resource):

    representations = {
        ContentFormat.TEXT: b"Welcome to the demo server",
        ContentFormat.LINKFORMAT: b"</.well-known/core>,ct=40",
        # ad-hoc for application/xhtml+xml;charset=utf-8
        ContentFormat(65000): b'<html xmlns="http://www.w3.org/1999/xhtml">'
        b"<head><title>aiocoap demo</title></head>"
        b"<body><h1>Welcome to the aiocoap demo server!</h1>"
        b'<ul><li><a href="time">Current time</a></li>'
        b'<li><a href="whoami">Report my network address</a></li>'
        b"</ul></body></html>",
    }

    default_representation = ContentFormat.TEXT

    async def render_get(self, request):
        cf = (
            self.default_representation
            if request.opt.accept is None
            else request.opt.accept
        )

        try:
            return aiocoap.Message(payload=self.representations[cf], content_format=cf)

        except KeyError:
            raise aiocoap.error.UnsupportedContentFormat # type: ignore


class TimeResource(resource.ObservableResource):
    """Example resource that can be observed. The `notify` method keeps
    scheduling itself, and calls `update_state` to trigger sending
    notifications."""

    def __init__(self):
        super().__init__()
        self.handle = None


    def notify(self):
        self.updated_state()
        self.reschedule()


    def reschedule(self):
        self.handle = asyncio.get_event_loop().call_later(5, self.notify)


    def update_observation_count(self, count):
        if count and self.handle is None:
            print("Starting the clock")
            self.reschedule()

        if count == 0 and self.handle:
            print("Stopping the clock")
            self.handle.cancel()
            self.handle = None


    async def render_get(self, request):
        payload = datetime.datetime.now().strftime("%Y-%m-%d %H:%M").encode("ascii")
        return aiocoap.Message(payload=payload)


class WhoAmI(resource.Resource):
    async def render_get(self, request):
        text = ["Used protocol: %s." % request.remote.scheme]

        text.append("Request came from %s." % request.remote.hostinfo)
        text.append("The server address used %s." % request.remote.hostinfo_local)

        claims = list(request.remote.authenticated_claims)

        if claims:
            text.append(
                "Authenticated claims of the client: %s."
                % ", ".join(repr(c) for c in claims)
            )
        else:
            text.append("No claims authenticated.")

        return aiocoap.Message(content_format=0, payload="\n".join(text).encode("utf8"))


async def loop_coap():
    # Resource tree creation
    root = resource.Site()
    sensor = resource.Site()


    # .well.known/* resources
    # CoRE protocol allows for automatic discovery of all endpoints
    # this server provides
    root.add_resource(
        [".well-known", "core"], resource.WKCResource(root.get_resources_as_linkheader)
    )

    # /* resources
    root.add_resource([], Welcome())
    root.add_resource(["time"], TimeResource())
    root.add_resource(["whoami"], WhoAmI())
    #root.add_resource([''], MQTT_Relay())

    # sensor/* resources
    root.add_resource(['sensor'], sensor)
    sensor.add_resource(['data'], MQTT_Relay())

    # 5683 is the port for unencrypted coap
    # 5684 is the port for DTLS coap
    await aiocoap.Context.create_server_context(root, bind=('localhost', 5683))

    # Run forever
    await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    try: 
        parser = argparse.ArgumentParser(description="A CoAP server that relays messages to an MQTT Broker")

        args = parser.parse_args()

        logging.info("---")
        logging.info(f"aiocoap Version: {version('aiocoap')}")
        logging.info(f"paho-mqtt Version: {version('paho-mqtt')}")
        logging.info("---")

        try: 
            MQTT_Relay.connect_mqtt(
                os.environ.get("MQTT_SERVER", "mqtt")#,
                #username=os.environ.get("MQTT_USER", None),
                #password=os.environ.get("MQTT_PASSWORD", None)
            )
        except Exception as e:
            logging.exception(f"Can't connect to MQTT: \"{e}\"")
            

        asyncio.run(loop_coap())
    
    except KeyboardInterrupt: 
        print("CoAP MQTT Bridge stopped")
