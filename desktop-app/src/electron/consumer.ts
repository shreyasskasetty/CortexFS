import amqp from "amqplib";
import { BrowserWindow, ipcMain } from "electron";
import { ipcWebContent } from "./util.js";

export const startRabbitMQConsumer = async (mainWindow: BrowserWindow, db: any) => {
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
                    const messageContent = msg.content.toString(); // Convert Buffer to string
                    console.log(`[x] Received: ${messageContent}`);

                    try {
                        // Parse the message as JSON
                        const message = JSON.parse(messageContent);

                        // // Insert into the database
                        // db.prepare(`
                        //     INSERT INTO suggestions (content) VALUES (?)
                        // `).run(messageContent);

                        // Acknowledge the message
                        channel.ack(msg);

                        // Send the parsed message to the Renderer process
                        handleMessageInRenderer(mainWindow, message, db);
                    } catch (error) {
                        console.error("Failed to parse message content:", error);
                        channel.nack(msg); // Negative acknowledgment if parsing fails
                    }
                }
            },
            { noAck: false }
        );
    } catch (error) {
        console.error("RabbitMQ consumer error:", error);
    }
};

function addNewSuggestion(suggestion: any, db: any) {
    // Insert into database
    db.prepare(`
        INSERT INTO suggestions (fileName, fileSize, downloadDate, currentPath, summary, suggestedPaths)
        VALUES (?, ?, ?, ?, ?, ?)
    `).run(
        suggestion.fileName,
        suggestion.size,
        suggestion.downloadDate,
        suggestion.srcPath,
        suggestion.summary,
        JSON.stringify(suggestion.suggestions) // Serialize the array as a JSON string
    );
}

const handleMessageInRenderer = (mainWindow: BrowserWindow, message: any, db: any) => {
    // Use Electron's IPC to send the message to the Renderer process
    // console.log("Sending message to Renderer process:", message);
    addNewSuggestion(message, db);
    ipcWebContent("suggestions", mainWindow.webContents, message);
    ipcWebContent("showNotification", mainWindow.webContents, {title: `Path Suggestions for ${message.fileName}`, body: `Suggested paths: ${message.suggestions.join(", ")}`});
};
