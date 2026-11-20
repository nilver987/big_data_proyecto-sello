import json
import os
import time

from kafka import KafkaConsumer


TOPIC_HELADAS = os.getenv("KAFKA_TOPIC_HELADAS", "heladas-eventos")
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "uso-heladas-group")
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

# Rango físicamente plausible para Juliaca. Más ancho que lo observado en el
# histórico (temperatura de -5.4 a 22.0 °C): fuera de aquí hay un dato corrupto.
RANGO_FISICO = {
    "temperatura": (-30.0, 40.0),
    "puntoRocio": (-60.0, 30.0),
    "humedad": (0.0, 100.0),
    "nubosidad": (0.0, 100.0),
}


def fuera_de_rango(event):
    for variable, (minimo, maximo) in RANGO_FISICO.items():
        valor = event.get(variable)
        if valor is not None and not (minimo <= valor <= maximo):
            return True
    return False


def deserialize_message(value):
    text = value.decode("utf-8")
    try:
        return {
            "payload": json.loads(text),
            "raw": text,
            "isJson": True,
            "decodeError": None,
        }
    except json.JSONDecodeError as ex:
        return {
            "payload": None,
            "raw": text,
            "isJson": False,
            "decodeError": str(ex),
        }


consumer = KafkaConsumer(
    TOPIC_HELADAS,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id=GROUP_ID,
    value_deserializer=deserialize_message,
    key_deserializer=lambda key: key.decode("utf-8") if key is not None else None,
)

print(json.dumps({
    "service": "uso-heladas",
    "component": "consumer",
    "topic": TOPIC_HELADAS,
    "groupId": GROUP_ID,
    "bootstrapServers": BOOTSTRAP_SERVERS,
    "status": "listening",
}))

for msg in consumer:
    decoded = msg.value
    event = decoded["payload"] if decoded["isJson"] else {}
    timestamp = event.get("timestamp")
    processed_at = int(time.time() * 1000)
    latency_ms = processed_at - timestamp if timestamp is not None else None
    is_valid = (
        decoded["isJson"]
        and event.get("tipoEvento") is not None
        and event.get("ciudad") is not None
        and event.get("temperatura") is not None
        and event.get("puntoRocio") is not None
        and event.get("humedad") is not None
        and event.get("nubosidad") is not None
        and timestamp is not None
    )
    alerta = is_valid and fuera_de_rango(event)

    log = {
        "service": "uso-heladas",
        "component": "consumer",
        "topic": msg.topic,
        "partition": msg.partition,
        "offset": msg.offset,
        "key": msg.key,
        "groupId": GROUP_ID,
        "eventType": event.get("tipoEvento"),
        "ciudad": event.get("ciudad"),
        "temperatura": event.get("temperatura"),
        "puntoRocio": event.get("puntoRocio"),
        "humedad": event.get("humedad"),
        "nubosidad": event.get("nubosidad"),
        "timestamp": timestamp,
        "isValid": is_valid,
        "fueraDeRango": alerta,
        "processedAt": processed_at,
        "latencyMs": latency_ms,
        "rawPayload": decoded["raw"],
        "isJson": decoded["isJson"],
        "decodeError": decoded["decodeError"],
        "status": "alerta" if alerta else ("consumed" if is_valid else "invalid"),
    }

    print(json.dumps(log))
