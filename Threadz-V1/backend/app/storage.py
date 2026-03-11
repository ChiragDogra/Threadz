"""
AWS S3 Storage Service for Threadz Application
"""
import os
import uuid
import asyncio
from typing import Optional, BinaryIO, Tuple
from urllib.parse import quote
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import HTTPException, UploadFile, status
from PIL import Image
import io

from .config import settings
from .security import generate_secure_filename

class S3StorageService:
    """AWS S3 storage service with image optimization"""
    
    def __init__(self):
        self.bucket_name = settings.AWS_S3_BUCKET
        self.region = settings.AWS_REGION
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=self.region
            )
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✅ S3 connected to bucket: {self.bucket_name}")
        except (NoCredentialsError, ClientError) as e:
            print(f"❌ S3 connection failed: {e}")
            self.s3_client = None
    
    async def upload_design_image(self, file: UploadFile, optimize: bool = True) -> Tuple[str, str]:
        """
        Upload design image to S3 with optimization
        
        Returns:
            Tuple[str, str]: (s3_url, thumbnail_url)
        """
        if not self.s3_client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="S3 service not available"
            )
        
        try:
            # Read file content
            file_content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Generate secure filename
            original_filename = file.filename or "design"
            secure_filename = generate_secure_filename(original_filename)
            
            # Optimize image if requested
            if optimize:
                optimized_content = await self._optimize_image(file_content)
                thumbnail_content = await self._create_thumbnail(file_content)
            else:
                optimized_content = file_content
                thumbnail_content = file_content
            
            # Upload main image
            main_key = f"designs/{secure_filename}"
            main_url = await self._upload_to_s3(
                content=optimized_content,
                key=main_key,
                content_type=file.content_type
            )
            
            # Upload thumbnail
            thumbnail_key = f"thumbnails/{secure_filename}"
            thumbnail_url = await self._upload_to_s3(
                content=thumbnail_content,
                key=thumbnail_key,
                content_type="image/webp"
            )
            
            return main_url, thumbnail_url
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {str(e)}"
            )
    
    async def upload_ai_generated_image(self, image_bytes: bytes, prompt: str) -> str:
        """Upload AI generated image to S3"""
        if not self.s3_client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="S3 service not available"
            )
        
        try:
            # Generate filename from prompt
            filename = f"ai_generated_{uuid.uuid4().hex[:12]}.webp"
            key = f"ai-designs/{filename}"
            
            # Optimize AI generated image
            optimized_content = await self._optimize_image(image_bytes)
            
            return await self._upload_to_s3(
                content=optimized_content,
                key=key,
                content_type="image/webp"
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload AI image: {str(e)}"
            )
    
    async def generate_presigned_url(self, s3_url: str, expiration: int = 3600) -> str:
        """Generate presigned URL for secure access"""
        if not self.s3_client:
            return s3_url  # Return original URL if S3 not available
        
        try:
            # Extract key from S3 URL
            key = s3_url.split(f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/")[-1]
            
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            
            return presigned_url
            
        except Exception as e:
            print(f"Failed to generate presigned URL: {e}")
            return s3_url
    
    async def delete_file(self, s3_url: str) -> bool:
        """Delete file from S3"""
        if not self.s3_client:
            return False
        
        try:
            # Extract key from S3 URL
            key = s3_url.split(f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/")[-1]
            
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
            
        except Exception as e:
            print(f"Failed to delete file: {e}")
            return False
    
    async def _upload_to_s3(self, content: bytes, key: str, content_type: str) -> str:
        """Upload content to S3 and return URL"""
        # Upload to S3
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content,
            ContentType=content_type,
            ACL='public-read'  # Make publicly accessible
        )
        
        # Generate URL
        url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{quote(key)}"
        return url
    
    async def _optimize_image(self, image_content: bytes, max_size: int = 2048, quality: int = 85) -> bytes:
        """Optimize image for web"""
        try:
            # Open image
            img = Image.open(io.BytesIO(image_content))
            
            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if too large
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert to WebP for better compression
            output = io.BytesIO()
            img.save(output, format='WEBP', quality=quality, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            print(f"Image optimization failed: {e}")
            return image_content  # Return original if optimization fails
    
    async def _create_thumbnail(self, image_content: bytes, size: int = 400, quality: int = 80) -> bytes:
        """Create thumbnail from image"""
        try:
            # Open image
            img = Image.open(io.BytesIO(image_content))
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Create thumbnail
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            
            # Save as WebP
            output = io.BytesIO()
            img.save(output, format='WEBP', quality=quality, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            print(f"Thumbnail creation failed: {e}")
            return image_content  # Return original if thumbnail creation fails

# Global S3 storage service instance
s3_storage = S3StorageService()
