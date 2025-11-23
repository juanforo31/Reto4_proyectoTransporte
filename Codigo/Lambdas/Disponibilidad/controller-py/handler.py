import json
import boto3
from botocore.exceptions import ClientError
from sns_publisher import SNSPublisher, SNSPublisherError

class LambdaHandlerError(Exception):
    pass

class LambdaHandler:
    def __init__(self):
        self.lambda_client = boto3.client("lambda")
        self.publicador = SNSPublisher()
        self.topics = {
            "/dev/registrar-reserva": "arn:aws:sns:us-east-1:652276263254:RegistrarReserva"      
        }

    def handle(self, event):
        try:
            path = event.get("rawPath", "")
            method = event.get("requestContext", {}).get("http", {}).get("method", "")
            signatureH = event.get("headers", {}).get("x-signature", "")

            if method == "GET":
                return self._handle_get(path)
            elif method == "POST":
                return self._handle_post(path, signatureH, method, event)
            else:
                return self.respuesta(405, {"error": f"Método {method} no permitido"})

        except SNSPublisherError as e:
            return self.respuesta(500, {"error": str(e)})
        except LambdaHandlerError as e:
            return self.respuesta(400, {"error": str(e)})
        except Exception as e:
            return self.respuesta(500, {"error": str(e)})

    def _handle_get(self, path):
        if path != "/dev/obtener-inventario":
            return self.respuesta(405, {"error": "Método GET no permitido en esta ruta"})

        topic_arn = self.topics[path]
        mensaje = {
            "mensaje": "Solicitud de inventario recibida",
            "path": path,
            "metodo": "GET"
        }

        try:
            response = self.lambda_client.invoke(
                FunctionName="ObtenerInventario",
                InvocationType="RequestResponse",
                Payload=json.dumps(mensaje)
            )
            payload = json.load(response["Payload"])
            return self.respuesta(200, {
                "mensaje": "Inventario obtenido correctamente",
                "data": payload
            })
        except ClientError as e:
            raise LambdaHandlerError(f"Error al invocar la Lambda de inventario: {e.response['Error']['Message']}")
        except Exception as e:
            raise LambdaHandlerError(f"Error inesperado al obtener inventario: {str(e)}")

    def _handle_post(self, path, signatureH, method, event):
        print("event:", event)
        raw_body = event['body']

        # Parse the JSON string into a Python dictionary
        try:    
            parsed_body = json.loads(raw_body)
            # Now you can access elements from the parsed_body, e.g., parsed_body['user_data']
            message = f"Received data: {parsed_body}"
            print(message)  # Log the received data
        except json.JSONDecodeError:
            # Handle cases where the body is not valid JSON
            message = f"Received non-JSON body: {raw_body}"
            print(message)  # Log the error message
            return self.respuesta(400, {"error": message})

        if path not in self.topics:
            return self.respuesta(404, {"error": "Ruta no encontrada"})

        topic_arn = self.topics[path]
        mensaje = {
            "mensaje": "Orden registrada correctamente",
            "path": path,
            "signature": signatureH,
            "metodo": method,
            "data": parsed_body
        }

        try:
            response = self.publicador.publish(topic_arn, mensaje)
            return self.respuesta(200, {
                "mensaje": "Orden procesada correctamente",
                "sns_message_id": response.get("MessageId")
            })
        except SNSPublisherError as e:
            raise
        except Exception as e:
            raise SNSPublisherError(f"Error al publicar en SNS: {str(e)}")

    def respuesta(self, status_code, body):
        return {
            "statusCode": status_code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body)
        }