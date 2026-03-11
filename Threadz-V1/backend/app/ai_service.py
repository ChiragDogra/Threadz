"""
AI Generation Service for Threadz Application
"""
import os
import uuid
import asyncio
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import stability_sdk
from stability_sdk.interfaces.generation import generation
from stability_sdk import client
import openai
from PIL import Image
import io

from .config import settings
from .storage import s3_storage
from .sentry_config import sentry_manager

class AIService:
    """AI service supporting multiple providers (Stability AI, OpenAI)"""
    
    def __init__(self):
        self.stability_client = None
        self.openai_client = None
        
        # Initialize Stability AI
        if settings.STABILITY_API_KEY:
            try:
                self.stability_client = client.StabilityInference(
                    key=settings.STABILITY_API_KEY,
                    verbose=False,
                    engine="stable-diffusion-xl-1024-v1-0"  # Use the latest model
                )
                print("✅ Stability AI client initialized")
            except Exception as e:
                print(f"❌ Stability AI initialization failed: {e}")
        
        # Initialize OpenAI
        if settings.OPENAI_API_KEY:
            try:
                self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                print("✅ OpenAI client initialized")
            except Exception as e:
                print(f"❌ OpenAI initialization failed: {e}")
        
        if not self.stability_client and not self.openai_client:
            print("⚠️ No AI service available - please configure API keys")
    
    async def generate_design(
        self, 
        prompt: str, 
        style: str = "realistic",
        width: int = 1024,
        height: int = 1024,
        samples: int = 1
    ) -> bytes:
        """
        Generate design image using available AI service
        
        Returns:
            bytes: Generated image data
        """
        if not self.stability_client and not self.openai_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI generation service not available"
            )
        
        try:
            # Try Stability AI first
            if self.stability_client:
                return await self._generate_with_stability_ai(prompt, style, width, height, samples)
            
            # Fallback to OpenAI DALL-E
            elif self.openai_client:
                return await self._generate_with_openai(prompt, style, width, height)
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "prompt": prompt[:100],  # Limit prompt length for privacy
                "style": style,
                "service": "ai_generation"
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI generation failed: {str(e)}"
            )
    
    async def _generate_with_stability_ai(
        self, 
        prompt: str, 
        style: str,
        width: int, 
        height: int, 
        samples: int
    ) -> bytes:
        """Generate image using Stability AI"""
        try:
            # Enhanced prompt based on style
            enhanced_prompt = self._enhance_prompt_for_style(prompt, style)
            
            # Generate image
            answers = self.stability_client.generate(
                prompt=enhanced_prompt,
                seed=uuid.uuid4().int,
                steps=30,
                cfg_scale=7.0,
                width=width,
                height=height,
                samples=samples,
                sampler=generation.SAMPLER_K_DPMPP_2M
            )
            
            # Process response
            for resp in answers:
                for artifact in resp.artifacts:
                    if artifact.type == generation.ARTIFACT_IMAGE:
                        return artifact.binary
            
            raise Exception("No image generated")
            
        except Exception as e:
            print(f"Stability AI generation failed: {e}")
            # Try OpenAI as fallback
            if self.openai_client:
                return await self._generate_with_openai(prompt, style, width, height)
            raise
    
    async def _generate_with_openai(
        self, 
        prompt: str, 
        style: str,
        width: int, 
        height: int
    ) -> bytes:
        """Generate image using OpenAI DALL-E"""
        try:
            # Enhanced prompt for DALL-E
            enhanced_prompt = self._enhance_prompt_for_style(prompt, style)
            
            # Generate image
            response = await self.openai_client.images.generate(
                prompt=enhanced_prompt,
                n=1,
                size=f"{width}x{height}" if f"{width}x{height}" in ["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] else "1024x1024",
                model="dall-e-3",
                quality="standard"
            )
            
            # Download image
            image_url = response.data[0].url
            import httpx
            async with httpx.AsyncClient() as client:
                image_response = await client.get(image_url)
                return image_response.content
                
        except Exception as e:
            print(f"OpenAI generation failed: {e}")
            raise
    
    def _enhance_prompt_for_style(self, prompt: str, style: str) -> str:
        """Enhance prompt based on selected style"""
        style_enhancements = {
            "realistic": "photorealistic, high quality, detailed, professional photography",
            "artistic": "digital art, artistic, creative, expressive, stylized",
            "minimalist": "minimalist, clean, simple, modern, elegant",
            "vintage": "vintage, retro, classic, aged, nostalgic",
            "abstract": "abstract, geometric, conceptual, modern art",
            "cartoon": "cartoon style, animated, colorful, fun, playful",
            "fantasy": "fantasy, magical, ethereal, mystical, imaginative"
        }
        
        enhancement = style_enhancements.get(style.lower(), "high quality, detailed")
        
        # Combine prompt with style enhancement
        if style.lower() in ["realistic", "photorealistic"]:
            return f"{prompt}, {enhancement}, 8k, ultra detailed, professional lighting"
        else:
            return f"{prompt}, {enhancement}, high quality, detailed"
    
    async def generate_and_upload(
        self, 
        prompt: str, 
        style: str = "realistic",
        design_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate design and upload to S3
        
        Returns:
            Dict with image_url, thumbnail_url, metadata
        """
        try:
            # Generate image
            image_bytes = await self.generate_design(prompt, style, 1024, 1024)
            
            # Upload to S3
            image_url = await s3_storage.upload_ai_generated_image(image_bytes, prompt)
            
            # Generate thumbnail
            thumbnail_url = await self._generate_thumbnail(image_bytes, prompt)
            
            # Extract metadata
            metadata = await self._extract_image_metadata(image_bytes)
            
            return {
                "image_url": image_url,
                "thumbnail_url": thumbnail_url,
                "metadata": metadata,
                "prompt": prompt,
                "style": style,
                "design_id": design_id
            }
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "prompt": prompt[:100],
                "style": style,
                "design_id": design_id,
                "service": "ai_generation_and_upload"
            })
            raise
    
    async def _generate_thumbnail(self, image_bytes: bytes, prompt: str) -> str:
        """Generate thumbnail and upload to S3"""
        try:
            # Create thumbnail using storage service
            thumbnail_bytes = await s3_storage._create_thumbnail(image_bytes, 400, 80)
            
            # Upload thumbnail
            filename = f"thumbnail_{uuid.uuid4().hex[:12]}.webp"
            key = f"thumbnails/{filename}"
            
            return await s3_storage._upload_to_s3(
                content=thumbnail_bytes,
                key=key,
                content_type="image/webp"
            )
            
        except Exception as e:
            print(f"Thumbnail generation failed: {e}")
            # Return main image URL as fallback
            return await s3_storage.upload_ai_generated_image(image_bytes, prompt)
    
    async def _extract_image_metadata(self, image_bytes: bytes) -> Dict[str, Any]:
        """Extract metadata from generated image"""
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "size_bytes": len(image_bytes)
                }
        except Exception as e:
            print(f"Metadata extraction failed: {e}")
            return {
                "width": 1024,
                "height": 1024,
                "format": "Unknown",
                "mode": "Unknown",
                "size_bytes": len(image_bytes)
            }
    
    def get_available_styles(self) -> list:
        """Get list of available generation styles"""
        return [
            {"id": "realistic", "name": "Photorealistic", "description": "Realistic photographic style"},
            {"id": "artistic", "name": "Artistic", "description": "Creative digital art style"},
            {"id": "minimalist", "name": "Minimalist", "description": "Clean and simple design"},
            {"id": "vintage", "name": "Vintage", "description": "Retro and classic style"},
            {"id": "abstract", "name": "Abstract", "description": "Modern abstract art"},
            {"id": "cartoon", "name": "Cartoon", "description": "Fun cartoon style"},
            {"id": "fantasy", "name": "Fantasy", "description": "Magical and imaginative"}
        ]
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.stability_client is not None or self.openai_client is not None

# Global AI service instance
ai_service = AIService()
