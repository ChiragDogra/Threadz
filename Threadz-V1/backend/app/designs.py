import os
import shutil
import uuid
import asyncio
from typing import Optional, List, Dict
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from . import models, schemas_design, auth
from .database import get_db

router = APIRouter(prefix="/api/v1/designs", tags=["designs"])

UPLOAD_DIR = "uploads/designs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=schemas_design.DesignResponse, status_code=status.HTTP_201_CREATED)
async def upload_design(
    file: UploadFile = File(...),
    design_name: str = Form(...),
    is_public: bool = Form(False),
    tags: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    user = current_user

    # File validation
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    file_ext = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Simplified mock for image size/dpi
    file_size_kb = os.path.getsize(file_path) // 1024

    new_design = models.Design(
        user_id=user.user_id,
        design_name=design_name,
        design_source="upload",
        image_url=f"/api/v1/uploads/designs/{unique_filename}",
        is_public=is_public,
        tags=tags,
        file_size_kb=file_size_kb,
        width_px=800, # Mocked
        height_px=800, # Mocked
        dpi=300 # Mocked
    )

    db.add(new_design)
    await db.commit()
    await db.refresh(new_design)

    return new_design

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
