from handler import LambdaHandler

def lambda_handler(event, context):
    handler = LambdaHandler()
    return handler.handle(event)