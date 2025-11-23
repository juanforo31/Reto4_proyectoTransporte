import json
import hmac
import hashlib
from config import SECRET_KEY
from exceptions import SignatureError

class Signature:
    """
    Realiza la validación de firmas HMAC-SHA256 para los mensajes entrantes.

    Esta clase realiza la verificacion de mensajes asegurando la integridad y 
    autenticidad del mensaje recibido, comparando el hash calculado con el 
    valor de la cabecera X-Signature.
    """
    def _init_(self, mesagge):
        """
        Inicializa la clase Signature con el mensaje que contiene la firma.

        Args:
            message (dict): Mensaje que contiene la firma a comparar.
        """
        self.mesagge = mesagge

    def checkSignature(self):
        """
        Realiza la comparacion entre el hash calculado y el valor de la cabecera
        X-Signature. 
        Returns:
            str: Mensaje indicando el resultado de la operación.

        Raises:
            SignatureError: Si ocurre un error en la validacion de la firma.
        """
        try:
            body = self.mesagge.get("body", {})
            body_raw = json.dumps(body, separators=(',', ':'))
            signatureH = self.mesagge.get("signature", "")
            recalculated_hash = hmac.new(SECRET_KEY, body_raw.encode("utf-8"), hashlib.sha256).hexdigest()

            if not hmac.compare_digest(signatureH, recalculated_hash):
                signatureH = "Invalida"
            else:
                signatureH = self.mesagge.get("signature", "")

            return signatureH
        except Exception as e:
            raise SignatureError(f"Error en la validacion de la firma: {str(e)}")