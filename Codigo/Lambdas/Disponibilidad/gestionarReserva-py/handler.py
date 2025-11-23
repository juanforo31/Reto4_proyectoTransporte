import boto3
import os
import json
import random
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

TABLE_NAME = os.environ.get("TABLE_NAME")
HEARTBEAT_TARGET = os.environ.get("HEARTBEAT_TARGET")
SOURCE_NAME = os.environ.get("SOURCE_NAME")

def lambda_handler(event, context):
    # Si viene de EventBridge (heartbeat programado)
    if event.get("source") == "aws.events":
        return send_heartbeat(context)

    # Si viene de API Gateway (reserva)
    return register_reservation(event)

def register_reservation(event):
    table = dynamodb.Table(TABLE_NAME)
    reservation_id = int(datetime.utcnow().timestamp())

    body = {}
    if "body" in event:
        try:
            body = json.loads(event["body"])
        except Exception:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Body inválido"})
            }

    item = {
        "id": reservation_id,
        "user": body.get("user", "anonymous"),
        "Asiento": body.get("Asiento"),
        "BusId": body.get("BusId"),
        "CiudadLlegada": body.get("CiudadLlegada"),
        "CiudadSalida": body.get("CiudadSalida"),
        "Pago": body.get("Pago", False),
        "UsuarioId": body.get("UsuarioId"),
        "timestamp": datetime.utcnow().isoformat()
    }

    table.put_item(Item=item)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Reserva registrada",
            "id": reservation_id
        })
    }

def send_heartbeat(context):
    simulated_status = 200 if random.random() < 0.5 else 400

    payload = {
        "type": "heartbeat",
        "source": SOURCE_NAME,
        "url": os.environ.get("SOURCE_URL"),
        "timestamp": datetime.utcnow().isoformat(),
        "statusCode": simulated_status,
        "arn": context.invoked_function_arn
    }


    response = lambda_client.invoke(
        FunctionName=HEARTBEAT_TARGET,
        InvocationType="Event",
        Payload=json.dumps(payload)
    )

    return {
        "status": "heartbeat_sent",
        "source": SOURCE_NAME,
        "details": str(response)
    }
