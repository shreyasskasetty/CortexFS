import os
import json
from typing import Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from langchain_core.documents import Document
import pika
import asyncio
import aio_pika

class WatchdogHandler(FileSystemEventHandler):
    def __init__(self, producer):
        self.producer = producer

    def on_created(self, event):
        self.producer.on_created(event)
        
class FileEventProducer:
    def __init__(self, rabbitmq_url, queue_name, organizer, summarizer):
        self.organizer = organizer
        self.summarizer = summarizer
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.directory_to_watch = None
        self.target_directory = None
        self.connection = None
        self.channel = None

    async def connect_to_rabbitmq(self):
        """Establish an asynchronous connection to RabbitMQ."""
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()
        await self.channel.declare_queue(self.queue_name, durable=True)

    async def send_event(self, suggestion):
        """Send suggestions to the notification queue."""
        print(f"Sending the following suggestions to the queue: {suggestion}")
        message = json.dumps(suggestion)
        try:
            await self.channel.default_exchange.publish(
                aio_pika.Message(body=message.encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                routing_key=self.queue_name,
            )
            print(f"Notification sent!")
        except Exception as e:
            print(f"Failed to send notification: {str(e)}")

    async def get_suggestions(self, rel_file_path):
        """Find the destination path for the file."""
        full_file_path = os.path.join(self.directory_to_watch, rel_file_path)
        category = self.summarizer.get_file_category(full_file_path)
        if category:
            content = self.summarizer.process_file(full_file_path, category)
            document = Document(
                page_content=content,
                metadata={"file_name": rel_file_path, "source": self.directory_to_watch, "category": category},
            )
            print("Summarizing document")
            summary = await self.summarizer.summarize_document(document)
            print("Getting path suggestions")
            response = self.organizer.get_path_suggestions(self.target_directory, summary)
            response["summary"] = summary.get("summary")
            response['src_path'] = full_file_path
            return response
        return None

    def on_created(self, event):
        """Callback for file creation."""
        if not event.is_directory:
            file_path = os.path.relpath(event.src_path, self.directory_to_watch)
            print(f"File created: {file_path}")
            asyncio.create_task(self.process_file_async(file_path))  # Use create_task for non-blocking execution

    async def process_file_async(self, file_path):
        """Process the file asynchronously and send suggestions."""
        suggestion = await self.get_suggestions(file_path)
        if suggestion:
            await self.send_event(suggestion)
        else:
            print(f"No suggestions found for file: {file_path}")

    def start_monitoring(self, directory_to_watch, target_directory):
        """Start monitoring the directory."""
        if not os.path.exists(directory_to_watch):
            raise FileNotFoundError(f"Directory not found: {directory_to_watch}")

        self.directory_to_watch = directory_to_watch
        self.target_directory = target_directory
        handler = WatchdogHandler(self)
        self.observer = Observer()
        self.observer.schedule(handler, self.directory_to_watch, recursive=True)
        self.observer.start()
        print(f"Started monitoring directory: {self.directory_to_watch}")

    def stop_monitoring(self):
        """Stop monitoring the directory."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            print("Stopped monitoring directory.")
