import json
import os
import time
import urllib.parse
import urllib.request

from kafka import KafkaProducer


TOPIC_HELADAS = os.getenv("KAFKA_TOPIC_HELADAS", "heladas-eventos")
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
INTERVAL_MS = int(os.getenv("API_INTERVAL_MS", "900000"))
CIUDAD = os.getenv("CIUDAD", "Juliaca")
API_URL = "https://api.weatherapi.com/v1/current.json"
# La clave viene del .env por variable de entorno; si falta, falla a la vista
API_KEY = os.environ["WEATHERAPI_KEY"]


def consultar_api():
    query = urllib.parse.urlencode({"key": API_KEY, "q": CIUDAD})
    with urllib.request.urlopen(f"{API_URL}?{query}", timeout=10) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    key_serializer=lambda key: key.encode("utf-8"),
    value_serializer=lambda value: json.dumps(value).encode("utf-8"),
)

print(json.dumps({
    "service": "uso-heladas",
    "component": "producer",
    "bootstrapServers": BOOTSTRAP_SERVERS,
    "ciudad": CIUDAD,
    "intervalMs": INTERVAL_MS,
    "status": "connected",
}))

while True:
    try:
        actual = consultar_api()["current"]

        data = {
            "tipoEvento": "clima.lectura",
            "ciudad": CIUDAD,
            "temperatura": actual["temp_c"],
            "puntoRocio": actual["dewpoint_c"],
            "humedad": actual["humidity"],
            "nubosidad": actual["cloud"],
            "origen": "weatherapi",
            "observadoEn": actual["last_updated_epoch"] * 1000,
            "timestamp": int(time.time() * 1000),
        }

        metadata = producer.send(TOPIC_HELADAS, key=CIUDAD, value=data).get(timeout=10)

        log = {
            "service": "uso-heladas",
            "component": "producer",
            "topic": metadata.topic,
            "partition": metadata.partition,
            "offset": metadata.offset,
            "eventType": data["tipoEvento"],
            "ciudad": CIUDAD,
            "temperatura": data["temperatura"],
            "timestamp": data["timestamp"],
            "status": "published",
        }
    except Exception as ex:
        # Un fallo de red o de la API no debe tumbar el productor
        log = {
            "service": "uso-heladas",
            "component": "producer",
            "topic": TOPIC_HELADAS,
            "timestamp": int(time.time() * 1000),
            "status": "error",
            "error": str(ex),
        }

    print(json.dumps(log))
    time.sleep(INTERVAL_MS / 1000)
