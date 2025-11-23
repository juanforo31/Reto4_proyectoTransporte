from handler import LambdaHandler

def lambda_handler(event, context):
    print("✅ Lambda ejecutándose correctamente. Event recibido:", event)
    handler = LambdaHandler()
    return handler.handle(event)