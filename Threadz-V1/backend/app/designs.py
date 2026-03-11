import os
import shutil
import uuid
import asyncio
from typing import Optional, List, Dict
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from . import models, schemas_design, auth
from .database import get_db
from .security import sanitize_input, validate_design_name, generate_secure_filename
from .rate_limiter import check_rate_limit
from .storage import s3_storage
from .ai_service import ai_service
from .queue import job_queue

router = APIRouter(prefix="/api/v1/designs", tags=["designs"])

UPLOAD_DIR = "uploads/designs"
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
os.makedirs(UPLOAD_DIR, exist_ok=True)

def validate_file(file: UploadFile) -> bool:
    """Validate uploaded file for security"""
    if not file.content_type or not file.content_type.startswith("image/"):
        return False
    
    if file.filename:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return False
    
    return True

@router.post("/upload", response_model=schemas_design.DesignResponse, status_code=status.HTTP_201_CREATED)
async def upload_design(
    request: Request,
    file: UploadFile = File(...),
    design_name: str = Form(...),
    is_public: bool = Form(False),
    tags: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Rate limiting check
    check_rate_limit(request, limit=10, window=60)  # 10 uploads per minute
    
    user = current_user

    # Validate and sanitize design name
    if not validate_design_name(design_name):
        raise HTTPException(status_code=400, detail="Invalid design name. Only alphanumeric characters, spaces, and basic punctuation are allowed.")
    
    design_name = sanitize_input(design_name)

    # File validation
    if not validate_file(file):
        raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset position
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File size exceeds limit of {MAX_FILE_SIZE // (1024*1024)}MB")
    
    try:
        # Upload to S3 with optimization
        s3_url, thumbnail_url = await s3_storage.upload_design_image(file, optimize=True)
        
        # Get file size from S3 upload
        file_size_kb = file_size // 1024

        new_design = models.Design(
            user_id=user.user_id,
            design_name=design_name,
            design_source="upload",
            image_url=s3_url,
            thumbnail_url=thumbnail_url,
            is_public=is_public,
            tags=sanitize_input(tags) if tags else None,
            file_size_kb=file_size_kb,
            width_px=800, # Mocked - could be extracted from image
            height_px=800, # Mocked - could be extracted from image
            dpi=300 # Mocked
        )

        db.add(new_design)
        await db.commit()
        await db.refresh(new_design)

        return new_design
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save design: {str(e)}")

@router.post("/generate", response_model=schemas_design.DesignResponse, status_code=status.HTTP_201_CREATED)
async def generate_design(
    request: Request,
    background_tasks: BackgroundTasks,
    prompt: str = Form(...),
    style: str = Form("realistic"),
    is_public: bool = Form(False),
    tags: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Rate limiting check
    check_rate_limit(request, limit=5, window=300)  # 5 generations per 5 minutes
    
    user = current_user

    # Validate and sanitize prompt
    if not prompt or len(prompt.strip()) < 3:
        raise HTTPException(status_code=400, detail="Prompt must be at least 3 characters long")
    
    prompt = sanitize_input(prompt.strip())
    style = sanitize_input(style.strip())

    try:
        # Create initial design record
        new_design = models.Design(
            user_id=user.user_id,
            design_name=f"AI Generated: {prompt[:50]}...",
            design_source="ai",
            image_url="",  # Will be updated when generation completes
            thumbnail_url="",  # Will be updated when generation completes
            is_public=is_public,
            tags=sanitize_input(tags) if tags else None,
            file_size_kb=0,
            width_px=1024,
            height_px=1024,
            dpi=300
        )

        db.add(new_design)
        await db.commit()
        await db.refresh(new_design)

        # Queue AI generation job
        job_id = await job_queue.enqueue_ai_generation(
            design_id=new_design.design_id,
            prompt=prompt,
            style=style,
            user_id=user.user_id
        )

        return new_design

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start AI generation: {str(e)}")

@router.get("/generate/status/{job_id}")
async def get_generation_status(
    job_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get AI generation job status"""
    try:
        status_info = await job_queue.get_job_status(job_id)
        
        if not status_info:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if user owns this job
        if status_info.get("user_id") != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@router.get("/", response_model=List[schemas_design.DesignResponse])
async def explore_designs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    # Rate limiting check
    check_rate_limit(request, limit=100, window=60)  # 100 requests per minute
    
    try:
        query = select(models.Design).where(models.Design.is_public == True)
        
        if search:
            search_term = f"%{sanitize_input(search)}%"
            query = query.where(models.Design.design_name.ilike(search_term))
        
        query = query.order_by(models.Design.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        designs = result.scalars().all()
        
        return designs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch designs: {str(e)}")

@router.get("/my-designs", response_model=List[schemas_design.DesignResponse])
async def get_my_designs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Rate limiting check
    check_rate_limit(request, limit=100, window=60)
    
    try:
        query = select(models.Design).where(models.Design.user_id == current_user.user_id)
        query = query.order_by(models.Design.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        designs = result.scalars().all()
        
        return designs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch designs: {str(e)}")

@router.get("/{design_id}", response_model=schemas_design.DesignResponse)
async def get_design(
    design_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        query = select(models.Design).where(models.Design.design_id == design_id)
        result = await db.execute(query)
        design = result.scalars().first()
        
        if not design:
            raise HTTPException(status_code=404, detail="Design not found")
        
        return design
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch design: {str(e)}")

@router.delete("/{design_id}")
async def delete_design(
    design_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get design
        query = select(models.Design).where(models.Design.design_id == design_id)
        result = await db.execute(query)
        design = result.scalars().first()
        
        if not design:
            raise HTTPException(status_code=404, detail="Design not found")
        
        # Check ownership
        if design.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this design")
        
        # Delete from S3
        if design.image_url:
            await s3_storage.delete_file(design.image_url)
        
        if design.thumbnail_url and design.thumbnail_url != design.image_url:
            await s3_storage.delete_file(design.thumbnail_url)
        
        # Delete from database
        await db.delete(design)
        await db.commit()
        
        return {"message": "Design deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete design: {str(e)}")

@router.get("/{design_id}/download")
async def download_design(
    design_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate presigned URL for design download"""
    try:
        # Get design
        query = select(models.Design).where(models.Design.design_id == design_id)
        result = await db.execute(query)
        design = result.scalars().first()
        
        if not design:
            raise HTTPException(status_code=404, detail="Design not found")
        
        # Check ownership or public access
        if design.user_id != current_user.user_id and not design.is_public:
            raise HTTPException(status_code=403, detail="Not authorized to download this design")
        
        # Generate presigned URL
        download_url = await s3_storage.generate_presigned_url(design.image_url, expiration=3600)
        
        return {"download_url": download_url, "expires_in": 3600}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")

@router.get("/explore", response_model=schemas_design.DesignPaginatedResponse)
async def get_explore_designs(
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * limit
    
    # Get total count
    query = select(models.Design).where(models.Design.is_public == True)
    result = await db.execute(query)
    total_designs = len(result.scalars().all())

    # Get paginated data
    query = select(models.Design).where(models.Design.is_public == True).order_by(desc(models.Design.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    designs = result.scalars().all()

    total_pages = (total_designs + limit - 1) // limit

    return {
        "designs": designs,
        "current_page": page,
        "total_pages": total_pages,
        "total_designs": total_designs
    }

# --- AI Generation Mock (Polling Pattern) ---

class AIGenerateRequest(BaseModel):
    prompt: str
    style: str
    num_variations: int = 4

# In-memory dictionary to track jobs
ai_jobs: Dict[str, dict] = {}

async def simulate_stable_diffusion_generation(job_id: str, prompt: str, style: str, num_variations: int):
    # Simulate processing delay
    await asyncio.sleep(8)
    
    # Generic placeholder image for the generated designs (using an unsplash nature placeholder as a mock)
    # We will pretend these are our "Stable Diffusion" results based on the prompt
    designs = []
    for i in range(num_variations):
        # We append a random query parameter to ensure the images don't cache locally in the browser looking identical
        placeholder_url = f"https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=800&q=80&rand={job_id}_{i}"
        designs.append({
            "design_id": str(uuid.uuid4()),
            "image_url": placeholder_url,
            "thumbnail_url": placeholder_url, # Using same for simplicity
            "ai_prompt": prompt,
            "ai_style": style
        })
    
    ai_jobs[job_id]["status"] = "completed"
    ai_jobs[job_id]["designs"] = designs

@router.post("/generate-ai", status_code=status.HTTP_202_ACCEPTED)
async def generate_ai_design(
    request: AIGenerateRequest, 
    background_tasks: BackgroundTasks,
    # db: AsyncSession = Depends(get_db) # We skip requiring user auth for the mock endpoints to keep it seamless initially
):
    job_id = str(uuid.uuid4())
    
    ai_jobs[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "designs": []
    }
    
    # Offload the mock generation to a background task
    background_tasks.add_task(
        simulate_stable_diffusion_generation, 
        job_id, 
        request.prompt, 
        request.style, 
        request.num_variations
    )
    
    return {
        "job_id": job_id,
        "status": "processing",
        "estimated_time": 8,
        "message": "AI generation via Stable Diffusion in progress"
    }

@router.get("/ai-status/{job_id}")
async def get_ai_status(job_id: str):
    if job_id not in ai_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return ai_jobs[job_id]
