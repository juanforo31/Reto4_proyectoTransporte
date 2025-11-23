import json
import boto3
from botocore.exceptions import ClientError

class SNSPublisherError(Exception):
    pass

class SNSPublisher:
    """
    Publicador de mensajes hacia tópicos de SNS (Simple Notification Service)
    en formato JSON
    """
    def __init__(self):
        """
        Inicializador del cliente SNS 
        """
        self.sns = boto3.client("sns")

    def publish(self, topic_arn, message):
        """
        Publica el mensaje en el topico SNS correspondiente 
        Args:
            topic_arn (str): ARN del tópico SNS al cual se enviará el mensaje.
            message (dict): Contenido del mensaje a publicar. Debe ser serializable a JSON.

        Returns:
            dict: Topico al que pertenece y mensaje con la informacion necesaria.

        Raises:
            SNSPublisherError: Si ocurre un error durante la publicación del mensaje a la cola.
        """
        try:
            response = self.sns.publish(
                TopicArn=topic_arn,
                Message=json.dumps(message)
            )
            return response
        except ClientError as e:
            raise SNSPublisherError(f"Error al publicar en SNS: {e.response['Error']['Message']}")
        except Exception as e:
            raise SNSPublisherError(f"Error inesperado publicando en SNS: {str(e)}")