import asyncio
from collections import deque
from typing import Dict, Optional, Tuple
import uuid
import time

class TranscriptionQueue:
    def __init__(self):
        self.queue = deque()
        self.current_user: Optional[str] = None
        self.lock = asyncio.Lock()
        self.condition = asyncio.Condition(self.lock)

    async def add_to_queue(self, user_id: str) -> Tuple[int, str]:
        async with self.lock:
            queue_token = str(uuid.uuid4())
            self.queue.append((user_id, queue_token))
            # Position doit compter le slot occupé + la file d'attente
            position = len(self.queue) + (1 if self.current_user is not None else 0)
            return position, queue_token

    async def get_queue_position(self, queue_token: str) -> Optional[int]:
        async with self.lock:
            offset = 1 if self.current_user is not None else 0
            for i, (user_id, token) in enumerate(self.queue):
                if token == queue_token:
                    return i + 1 + offset
            return None

    async def acquire_transcription_slot(self, queue_token: str) -> bool:
        """Try to acquire transcription slot, return True if acquired, False if not found in queue"""
        async with self.lock:
            # Check if there's already a current user (slot is taken)
            if self.current_user is not None:
                return False

            # Check if this token is at the front of the queue
            if len(self.queue) > 0 and self.queue[0][1] == queue_token:
                # Remove from queue and set as current user
                self.current_user = self.queue.popleft()[0]
                return True
            return False

    async def release_transcription_slot(self):
        """Release the current transcription slot"""
        async with self.lock:
            self.current_user = None

    async def get_current_queue_info(self) -> Dict:
        """Get current queue information"""
        async with self.lock:
            return {
                "current_user": self.current_user,
                "queue_length": len(self.queue),
                "is_busy": self.current_user is not None
            }

# Global queue instance
transcription_queue = TranscriptionQueue()