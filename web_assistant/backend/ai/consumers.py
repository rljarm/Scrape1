"""WebSocket consumers for the AI app."""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ProcessingTask, SearchQuery, YouTubeData

class ProcessingTaskConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for AI processing task updates."""

    async def connect(self):
        """Handle WebSocket connection."""
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.task_group_name = f'task_{self.task_id}'

        # Join task group
        await self.channel_layer.group_add(
            self.task_group_name,
            self.channel_name
        )

        # Accept the connection
        await self.accept()

        # Send initial task state
        task = await self.get_task()
        if task:
            await self.send_task_update(task)

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.task_group_name,
            self.channel_name
        )

    async def task_update(self, event):
        """Handle task update messages."""
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def get_task(self):
        """Get task details from database."""
        try:
            task = ProcessingTask.objects.get(id=self.task_id)
            return {
                'id': task.id,
                'status': task.status,
                'error_message': task.error_message,
                'processing_time': task.processing_time,
            }
        except ProcessingTask.DoesNotExist:
            return None

    async def send_task_update(self, task_data):
        """Send task update to client."""
        if task_data:
            await self.send(text_data=json.dumps({
                'type': 'task_update',
                'data': task_data
            }))
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Task not found'
            }))

class SearchQueryConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for search query updates."""

    async def connect(self):
        """Handle WebSocket connection."""
        self.query_id = self.scope['url_route']['kwargs']['query_id']
        self.query_group_name = f'search_{self.query_id}'

        await self.channel_layer.group_add(
            self.query_group_name,
            self.channel_name
        )
        await self.accept()

        # Send initial query state
        query = await self.get_query()
        if query:
            await self.send_query_update(query)

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.query_group_name,
            self.channel_name
        )

    async def search_update(self, event):
        """Handle search update messages."""
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def get_query(self):
        """Get query details from database."""
        try:
            query = SearchQuery.objects.get(id=self.query_id)
            return {
                'id': query.id,
                'status': query.status,
                'results_count': len(query.results),
                'error_message': query.error_message,
            }
        except SearchQuery.DoesNotExist:
            return None

    async def send_query_update(self, query_data):
        """Send query update to client."""
        if query_data:
            await self.send(text_data=json.dumps({
                'type': 'search_update',
                'data': query_data
            }))
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Query not found'
            }))

class YouTubeProcessingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for YouTube video processing updates."""

    async def connect(self):
        """Handle WebSocket connection."""
        self.video_id = self.scope['url_route']['kwargs']['video_id']
        self.video_group_name = f'video_{self.video_id}'

        await self.channel_layer.group_add(
            self.video_group_name,
            self.channel_name
        )
        await self.accept()

        # Send initial video state
        video = await self.get_video()
        if video:
            await self.send_video_update(video)

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.video_group_name,
            self.channel_name
        )

    async def video_update(self, event):
        """Handle video update messages."""
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def get_video(self):
        """Get video details from database."""
        try:
            video = YouTubeData.objects.get(id=self.video_id)
            return {
                'id': video.id,
                'ai_processed': video.ai_processed,
                'has_error': 'error' in video.ai_results,
                'results': video.ai_results if video.ai_processed else None,
            }
        except YouTubeData.DoesNotExist:
            return None

    async def send_video_update(self, video_data):
        """Send video update to client."""
        if video_data:
            await self.send(text_data=json.dumps({
                'type': 'video_update',
                'data': video_data
            }))
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Video not found'
            }))

class AIModelStatusConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for AI model status updates."""

    async def connect(self):
        """Handle WebSocket connection."""
        await self.channel_layer.group_add('ai_model_status', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard('ai_model_status', self.channel_name)

    async def model_status_update(self, event):
        """Handle model status update messages."""
        await self.send(text_data=json.dumps(event['data']))
