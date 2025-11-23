import os
import boto3
import json
from datetime import datetime, timezone

dynamodb = boto3.resource("dynamodb")
TABLA_ESTADO = os.environ["TABLA_ESTADO"]

def lambda_handler(event, context):
    print("=== EVENTO RECIBIDO ===")
    print(json.dumps(event))

    if event.get("type") == "heartbeat":
        print("[HANDLER] Entrando en manejar_latido")
        return manejar_latido(event)

    if event.get("source") == "aws.cloudwatch":
        print("[HANDLER] Entrando en manejar_failover")
        return manejar_failover()

    if event.get("httpMethod") == "GET" and event.get("path") == "/estado":
        print("[HANDLER] Entrando en manejar_consulta")
        return manejar_consulta()

    print("[HANDLER] Evento no reconocido")
    return {
        "statusCode": 400,
        "body": json.dumps({"mensaje": "Evento no reconocido"})
    }

def manejar_latido(event):
    print("=== MANEJAR LATIDO ===")
    origen = event.get("source")
    print(f"[LATIDO] origen: {origen}")

    ahora = datetime.now(timezone.utc).isoformat()
    print(f"[LATIDO] timestamp: {ahora}")

    url_lambda = event.get("url")
    print(f"[LATIDO] url_lambda: {url_lambda}")

    arn_lambda = event.get("arn")
    print(f"[LATIDO] arn_lambda: {arn_lambda}")
    
    statusCode  = event.get("statusCode")
    print(f"[LATIDO] statusCode: {statusCode}")

    tabla = dynamodb.Table(TABLA_ESTADO)
    print(f"[LATIDO] Actualizando tabla: {TABLA_ESTADO}")
    
    if statusCode != 200:
        resp = tabla.update_item(
        Key={"id": origen},
        UpdateExpression="SET ultimoLatido = :hb, estadoSalud = :st, nombreLambda = :ln, direccionLambda = :url, arn = :arn_lambda",
        ExpressionAttributeValues={
            ":hb": ahora,
            ":st": "fallando",
            ":ln": origen,
            ":url": url_lambda,
            ":arn": arn_lambda
        }
    )
    else:        
        resp = tabla.update_item(
            Key={"id": origen},
            UpdateExpression="SET ultimoLatido = :hb, estadoSalud = :st, nombreLambda = :ln, direccionLambda = :url, arn = :arn_lambda",
            ExpressionAttributeValues={
                ":hb": ahora,
                ":st": "saludable",
                ":ln": origen,
                ":url": url_lambda,
                ":arn_lambda": arn_lambda
            }
        )
    print(f"[LATIDO] Respuesta DynamoDB: {json.dumps(resp)}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "mensaje": f"Latido recibido de {origen}",
            "momento": ahora,
            "nombreLambda": origen,
            "direccionLambda": url_lambda
        })
    }

def manejar_failover():
    print("=== MANEJAR FAILOVER ===")
    tabla = dynamodb.Table(TABLA_ESTADO)
    ahora = datetime.now(timezone.utc).isoformat()
    print(f"[FAILOVER] timestamp: {ahora}")

    nueva_activa = os.environ["OBJETIVO_FAILOVER"]
    print(f"[FAILOVER] nueva_activa: {nueva_activa}")

    url_lambda = f"https://lambda-url.amazonaws.com/{nueva_activa}"
    print(f"[FAILOVER] url_lambda: {url_lambda}")

    resp = tabla.update_item(
        Key={"id": "lambdaActiva"},
        UpdateExpression="SET #v = :val, ultimoCambio = :sw, direccionLambda = :url, arn = :arn",
        ExpressionAttributeNames={"#v": "valor"},
        ExpressionAttributeValues={
            ":val": nueva_activa,
            ":sw": ahora,
            ":url": url_lambda,
        }
    )
    print(f"[FAILOVER] Respuesta DynamoDB: {json.dumps(resp)}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "mensaje": "Failover ejecutado",
            "nuevaActiva": nueva_activa,
            "momento": ahora,
            "direccionLambda": url_lambda
        })
    }

def manejar_consulta():
    print("=== MANEJAR CONSULTA ===")
    tabla = dynamodb.Table(TABLA_ESTADO)
    print(f"[CONSULTA] Leyendo item con id=lambdaActiva")

    resultado = tabla.get_item(Key={"id": "lambdaActiva"})
    print(f"[CONSULTA] Resultado DynamoDB: {json.dumps(resultado)}")

    if "Item" not in resultado:
        print("[CONSULTA] No se encontró estado activo")
        return {
            "statusCode": 404,
            "body": json.dumps({"mensaje": "No se encontró estado activo"})
        }

    item = resultado["Item"]
    print(f"[CONSULTA] Item encontrado: {json.dumps(item)}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "lambdaActiva": item["valor"],
            "direccionLambda": item.get("direccionLambda", f"https://lambda-url.amazonaws.com/{item['valor']}")
        })
    }