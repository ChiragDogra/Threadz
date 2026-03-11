"""
Background Job Queue System for Threadz Application
"""
import os
import uuid
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import redis.asyncio as redis
from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from .config import settings
from .database import get_db
from .models import Design
from .ai_service import ai_service
from .sentry_config import sentry_manager

# Redis connection for job queue
redis_client = None

# Celery configuration for complex tasks
celery_app = Celery(
    'threadz',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.queue']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

class JobQueue:
    """Redis-based job queue for AI generation and other background tasks"""
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.redis_client = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                decode_responses=True,
                max_connections=20
            )
            # Test connection
            await self.redis_client.ping()
            print("✅ Redis job queue initialized")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            self.redis_client = None
    
    async def enqueue_ai_generation(
        self, 
        design_id: str, 
        prompt: str, 
        style: str, 
        user_id: str
    ) -> str:
        """Enqueue AI generation job"""
        if not self.redis_client:
            raise Exception("Redis not available for job queue")
        
        job_id = str(uuid.uuid4())
        
        job_data = {
            "job_id": job_id,
            "type": "ai_generation",
            "design_id": design_id,
            "prompt": prompt,
            "style": style,
            "user_id": user_id,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None,
            "result": None
        }
        
        try:
            # Store job data
            await self.redis_client.hset(
                f"job:{job_id}",
                mapping=job_data
            )
            
            # Add to queue
            await self.redis_client.lpush("ai_generation_queue", job_id)
            
            # Set expiration (24 hours)
            await self.redis_client.expire(f"job:{job_id}", 86400)
            
            print(f"✅ AI generation job enqueued: {job_id}")
            return job_id
            
        except Exception as e:
            print(f"❌ Failed to enqueue job: {e}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status"""
        if not self.redis_client:
            return None
        
        try:
            job_data = await self.redis_client.hgetall(f"job:{job_id}")
            
            if not job_data:
                return None
            
            # Convert string values back to appropriate types
            if job_data.get("created_at"):
                job_data["created_at"] = datetime.fromisoformat(job_data["created_at"])
            if job_data.get("started_at"):
                job_data["started_at"] = datetime.fromisoformat(job_data["started_at"])
            if job_data.get("completed_at"):
                job_data["completed_at"] = datetime.fromisoformat(job_data["completed_at"])
            
            return job_data
            
        except Exception as e:
            print(f"❌ Failed to get job status: {e}")
            return None
    
    async def update_job_status(
        self, 
        job_id: str, 
        status: str, 
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """Update job status"""
        if not self.redis_client:
            return
        
        try:
            updates = {"status": status}
            
            if status == "started":
                updates["started_at"] = datetime.utcnow().isoformat()
            elif status in ["completed", "failed"]:
                updates["completed_at"] = datetime.utcnow().isoformat()
                if result:
                    updates["result"] = json.dumps(result)
                if error:
                    updates["error"] = error
            
            await self.redis_client.hset(f"job:{job_id}", mapping=updates)
            
        except Exception as e:
            print(f"❌ Failed to update job status: {e}")
    
    async def process_ai_generation_queue(self):
        """Process AI generation jobs from queue"""
        if not self.redis_client:
            return
        
        while True:
            try:
                # Get job from queue
                job_id = await self.redis_client.brpop("ai_generation_queue", timeout=1)
                
                if job_id:
                    job_id = job_id[1]  # brpop returns (key, value)
                    await self._process_ai_generation_job(job_id)
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                print(f"❌ Queue processing error: {e}")
                sentry_manager.capture_exception(e, {"service": "job_queue"})
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _process_ai_generation_job(self, job_id: str):
        """Process individual AI generation job"""
        try:
            # Get job data
            job_data = await self.get_job_status(job_id)
            if not job_data:
                return
            
            # Update status to started
            await self.update_job_status(job_id, "started")
            
            # Generate design
            result = await ai_service.generate_and_upload(
                prompt=job_data["prompt"],
                style=job_data["style"],
                design_id=job_data["design_id"]
            )
            
            # Update database with result
            await self._update_design_with_result(job_data["design_id"], result)
            
            # Update job status to completed
            await self.update_job_status(job_id, "completed", result=result)
            
            print(f"✅ AI generation job completed: {job_id}")
            
        except Exception as e:
            print(f"❌ AI generation job failed: {job_id} - {e}")
            
            # Update job status to failed
            await self.update_job_status(job_id, "failed", error=str(e))
            
            # Log to Sentry
            sentry_manager.capture_exception(e, {
                "job_id": job_id,
                "job_data": job_data,
                "service": "ai_generation_job"
            })
    
    async def _update_design_with_result(self, design_id: str, result: Dict[str, Any]):
        """Update design record with AI generation result"""
        try:
            # Get database session
            async with get_db() as db:
                # Get design
                query = select(Design).where(Design.design_id == design_id)
                db_result = await db.execute(query)
                design = db_result.scalars().first()
                
                if design:
                    # Update design with generated image URLs
                    design.image_url = result["image_url"]
                    design.thumbnail_url = result["thumbnail_url"]
                    design.width_px = result["metadata"]["width"]
                    design.height_px = result["metadata"]["height"]
                    design.file_size_kb = result["metadata"]["size_bytes"] // 1024
                    
                    await db.commit()
                    print(f"✅ Design updated with AI result: {design_id}")
                else:
                    print(f"❌ Design not found: {design_id}")
                    
        except Exception as e:
            print(f"❌ Failed to update design: {e}")
            raise
    
    async def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs"""
        if not self.redis_client:
            return
        
        try:
            # Get all job keys
            job_keys = await self.redis_client.keys("job:*")
            
            for job_key in job_keys:
                job_data = await self.redis_client.hgetall(job_key)
                
                if job_data:
                    created_at = datetime.fromisoformat(job_data.get("created_at", ""))
                    
                    # Check if job is old and completed
                    if (datetime.utcnow() - created_at > timedelta(hours=max_age_hours) and
                        job_data.get("status") in ["completed", "failed"]):
                        
                        await self.redis_client.delete(job_key)
                        print(f"🧹 Cleaned up old job: {job_key}")
                        
        except Exception as e:
            print(f"❌ Job cleanup failed: {e}")

# Celery tasks for complex background processing
@celery_app.task(bind=True)
def process_heavy_ai_generation(self, design_id: str, prompt: str, style: str, user_id: str):
    """Celery task for heavy AI generation (alternative to Redis queue)"""
    try:
        # Update task state
        self.update_state(state="PROCESSING", meta={"status": "Generating design..."})
        
        # Generate design (this would be a synchronous call in Celery)
        # For now, this is just a placeholder
        result = {
            "design_id": design_id,
            "status": "completed",
            "image_url": "https://example.com/generated.jpg"
        }
        
        return result
        
    except Exception as e:
        # Update task state with error
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "Generation failed"}
        )
        raise

# Global job queue instance
job_queue = JobQueue()

# Background task to start queue processor
async def start_queue_processor():
    """Start the background queue processor"""
    await job_queue.initialize()
    
    # Start queue processing in background
    asyncio.create_task(job_queue.process_ai_generation_queue())
    
    # Start cleanup task
    asyncio.create_task(schedule_cleanup())

async def schedule_cleanup():
    """Schedule periodic cleanup of old jobs"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            await job_queue.cleanup_old_jobs()
        except Exception as e:
            print(f"❌ Cleanup scheduling error: {e}")
            await asyncio.sleep(300)  # Retry after 5 minutes
