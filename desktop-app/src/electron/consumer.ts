import amqp from "amqplib";
import { ipcMain } from "electron";

export const startRabbitMQConsumer = async () => {
    const rabbitmqUrl = "amqp://localhost"; // Replace with your RabbitMQ URL
    const queueName = "suggestion-notifications";

    try {
        // Connect to RabbitMQ server
        const connection = await amqp.connect(rabbitmqUrl);
        const channel = await connection.createChannel();

        // Ensure the queue exists
        await channel.assertQueue(queueName, { durable: true });

        console.log(`[*] Waiting for messages in ${queueName}. To exit press CTRL+C`);

        // Consume messages
        channel.consume(
            queueName,
            (msg) => {
                if (msg !== null) {
                    const messageContent = msg.content.toString();
                    console.log(`[x] Received: ${messageContent}`);

                    // Acknowledge the message
                    channel.ack(msg);

                    // Process the message (send it to Renderer process, etc.)
                    handleMessageInRenderer(messageContent);
                }
            },
            { noAck: false }
        );
    } catch (error) {
        console.error("RabbitMQ consumer error:", error);
    }
};

const handleMessageInRenderer = (message: any) => {
    // Use Electron's IPC to send the message to the Renderer process
    console.log("Sending message to Renderer process:", message);
    // ipcMain.emit("message-from-rabbitmq", message); // Emit an event to Renderer
};
