import os
import json
from typing import Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from langchain_core.documents import Document
import pika
import asyncio
import aio_pika
import time
import threading

class WatchdogHandler(FileSystemEventHandler):
    def __init__(self, producer):
        self.producer = producer

    def on_created(self, event):
        self.producer.on_created(event)
        
class FileEventProducer:
    def __init__(self, rabbitmq_url, queue_name, organizer, summarizer, logger):
        self.logger = logger
        self.organizer = organizer
        self.summarizer = summarizer
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.directory_to_watch = None
        self.target_directory = None
        self.connection = None
        self.channel = None
        self.event_loop = None

    def log_task_result(self, future):
        """Log the result of a completed task."""
        try:
            result = future.result()  # Will raise an exception if the task failed
            self.logger.info(f"Task completed successfully: {result}")
        except Exception as e:
            self.logger.error(f"Task failed with exception: {e}")

    def start_event_loop(self):
        """Start a new asyncio event loop in a separate thread."""
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        self.logger.info("Starting new event loop for file monitoring...")
        self.event_loop.run_forever()

    def initialize_event_loop_thread(self):
        """Initialize the thread for the event loop."""
        self.thread = threading.Thread(target=self.start_event_loop, daemon=True)
        self.thread.start()
        self.logger.info("FileEventProducer event loop thread started.")

    def stop_event_loop(self):
        """Stop the event loop and thread."""
        if self.event_loop and self.thread:
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)
            self.thread.join()
            self.logger.info("FileEventProducer event loop thread stopped.")
    
    async def connect_to_rabbitmq(self):
        """Establish an asynchronous connection to RabbitMQ on the producer's event loop."""
        try:
            if not self.event_loop:
                raise RuntimeError("Event loop is not initialized for FileEventProducer.")

            # Run the connection on the producer's event loop
            future = asyncio.run_coroutine_threadsafe(self._connect_to_rabbitmq(), self.event_loop)
            future.add_done_callback(self.log_task_result)
            self.logger.info("Connected to RabbitMQ on the producer's event loop.")
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def _connect_to_rabbitmq(self):
        """Internal method to connect to RabbitMQ."""
        self.logger.info("Connecting to RabbitMQ...")
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()
        await self.channel.declare_queue(self.queue_name, durable=True)

    async def send_event(self, suggestion):
        """Send suggestions to the RabbitMQ queue."""
        try:
            self.logger.info(f"Sending the following suggestion: {suggestion}")
            message = json.dumps(suggestion)

            # Run on the producer's event loop
            future = asyncio.run_coroutine_threadsafe(self._send_message(message), self.event_loop)
            future.add_done_callback(self.log_task_result)
            self.logger.info("Notification sent successfully!")
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")

    async def _send_message(self, message):
        try:
            await asyncio.wait_for(
                self.channel.default_exchange.publish(
                    aio_pika.Message(body=message.encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                    routing_key=self.queue_name,
                ),
                timeout=10,  # Set a timeout for the operation
            )
        except asyncio.TimeoutError:
            self.logger.error("Failed to send message: Operation timed out.")

    async def get_suggestions(self, rel_file_path):
        """Find the destination path for the file."""
        full_file_path = os.path.join(self.directory_to_watch, rel_file_path)
        category = self.summarizer.get_file_category(full_file_path)
        if category:
            content = self.summarizer.process_file(full_file_path, category)
            # if category is json then do json dump
            if isinstance(content, dict):
                content = json.dumps(content)
            document = Document(
                page_content=content,
                metadata={"file_name": rel_file_path, "source": self.directory_to_watch, "category": category},
            )
            self.logger.info("Summarizing document")
            summary = await self.summarizer.summarize_document(document)
            self.logger.info("Getting path suggestions")
            response = self.organizer.get_path_suggestions(self.target_directory, summary)
            response["summary"] = summary.get("summary")
            response["fileName"] = rel_file_path
            response['srcPath'] = full_file_path
            response['size'] = os.path.getsize(full_file_path)
            response['downloadDate'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getctime(full_file_path)))
            
            return response
        return None

    def on_created(self, event):
        """Callback for file creation."""
        if not event.is_directory:
            file_path = os.path.relpath(event.src_path, self.directory_to_watch)
            self.logger.info(f"File created: {file_path}")
            time.sleep(1)
            try:
                future = asyncio.run_coroutine_threadsafe(self.process_file_async(file_path), self.event_loop)
                future.add_done_callback(self.log_task_result)
                self.logger.info(f"Scheduled process_file_async for {file_path}")
            except Exception as e:
                self.logger.info(f"Error scheduling process_file_async: {e}")
            # asyncio.create_task(self.process_file_async(file_path))  # Use create_task for non-blocking execution

    async def process_file_async(self, file_path):
        """Process the file asynchronously and send suggestions."""
        try:
            self.logger.info(f"Started processing file: {file_path}")
            suggestion = await self.get_suggestions(file_path)
            if suggestion:
                self.logger.info(f"Suggestion generated for {file_path}: {suggestion}")
                await self.send_event(suggestion)
            else:
                self.logger.info(f"No suggestions found for file: {file_path}")
        except Exception as e:
            self.logger.error(f"Error in process_file_async for {file_path}: {e}")

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
        self.logger.info(f"Started monitoring directory: {self.directory_to_watch}")

    def stop_monitoring(self):
        """Stop monitoring the directory."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.logger.info("Stopped monitoring directory.")
