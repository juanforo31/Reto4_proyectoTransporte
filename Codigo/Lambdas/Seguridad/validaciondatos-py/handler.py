import json
from signature import Signature
from exceptions import SignatureError

class LambdaHandler:
    """
    Handler simplificado: solo valida que el JSON sea válido 
    y que la firma HMAC coincida.
    """

    def handle(self, event):
        try:
            # Verificar que el evento sea dict
            if not isinstance(event, dict):
                return self.respuesta(400, {"error": "El evento recibido no es un JSON válido"})

            # Validación de firma
            try:
                signature = Signature(event)
                signatureValidation = signature.checkSignature()
            except SignatureError as e:
                return self.respuesta(400, {"error": str(e)})

            # Respuesta si la firma es inválida
            if signatureValidation == "Invalida":
                return self.respuesta(400, {
                    "RespuestaFirma": signatureValidation,
                    "Respuesta": "Firma inválida."
                })

            # Si todo OK
            return self.respuesta(200, {
                "RespuestaFirma": signatureValidation,
                "Respuesta": "JSON válido y firma correcta"
            })

        except Exception as e:
            return self.respuesta(500, {
                "error": f"Error interno del servidor: {str(e)}"
            })

    def respuesta(self, status, body):
        return {
            "statusCode": status,
            "body": json.dumps(body)
            }