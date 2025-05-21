# app/utils/mqtt_client.py
import json
import paho.mqtt.client as mqtt

class FarmbotMQTTClient:
    def __init__(self, on_status=None, token_path="farmbot_authorization_token.json"):
        with open(token_path, "r") as f:
            token_data = json.load(f)

        self.mqtt_host = token_data["token"]["unencoded"]["mqtt"]
        self.username = token_data["token"]["unencoded"]["bot"]
        self.password = token_data["token"]["encoded"]
        self.device_id = token_data["user"]["device_id"]
        self.on_status = on_status

        self.client = mqtt.Client()
        self.client.username_pw_set(self.username, self.password)
        self.client.on_message = self._on_message
        self.connected = False

    def connect(self):
        self.client.connect(self.mqtt_host, 1883, 60)
        self.client.subscribe(f"bot/{self.username}/status")
        self.client.loop_start()
        self.connected = True

    def _on_message(self, client, userdata, msg):
        if self.on_status:
            self.on_status(json.loads(msg.payload.decode()))

    def stop(self):
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
