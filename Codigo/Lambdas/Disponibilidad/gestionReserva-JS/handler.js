const AWS = require("aws-sdk");
const dynamodb = new AWS.DynamoDB.DocumentClient();
const lambda = new AWS.Lambda();

const TABLE_NAME = process.env.TABLE_NAME;
const HEARTBEAT_TARGET = process.env.HEARTBEAT_TARGET;
const SOURCE_NAME = process.env.SOURCE_NAME;
const SOURCE_URL = process.env.SOURCE_URL;

exports.lambdaHandler = async (event,context) => {
  // Si viene de EventBridge (heartbeat programado)
  if (event.source === "aws.events") {
    return await sendHeartbeat(context);
  }

  // Si viene de API Gateway (reserva)
  return await registerReservation(event);
};

async function registerReservation(event) {
  let body = {};
  if (event.body) {
    try {
      body = JSON.parse(event.body);
    } catch (err) {
      return {
        statusCode: 400,
        body: JSON.stringify({ message: "Body inválido" }),
      };
    }
  }

  const reservationId = Date.now();

  const item = {
    id: reservationId,
    user: body.user || "anonymous",
    Asiento: body.Asiento,
    BusId: body.BusId,
    CiudadLlegada: body.CiudadLlegada,
    CiudadSalida: body.CiudadSalida,
    Pago: body.Pago || false,
    UsuarioId: body.UsuarioId,
    timestamp: new Date().toISOString(),
  };

  await dynamodb.put({ TableName: TABLE_NAME, Item: item }).promise();

  return {
    statusCode: 200,
    body: JSON.stringify({
      message: "Reserva registrada",
      id: reservationId,
    }),
  };
}

async function sendHeartbeat(context) {

  let arn = context.invokedFunctionArn;

  const payload = {
    type: "heartbeat",
    source: SOURCE_NAME,
    url: SOURCE_URL,
    timestamp: new Date().toISOString(),
    statusCode: 200,
    arn: arn
  };

  await lambda
    .invoke({
      FunctionName: HEARTBEAT_TARGET,
      InvocationType: "Event",
      Payload: JSON.stringify(payload),
    })
    .promise();

  return {
    status: "heartbeat_sent",
    source: SOURCE_NAME,
  };
}
