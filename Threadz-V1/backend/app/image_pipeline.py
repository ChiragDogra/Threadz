"""
Advanced Image Optimization Pipeline for Threadz Application
"""
import os
import io
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter
import hashlib
from datetime import datetime
from fastapi import HTTPException, status
from dataclasses import dataclass

from .storage import s3_storage
from .sentry_config import sentry_manager

@dataclass
class ImageDimensions:
    """Image dimensions configuration"""
    width: int
    height: int
    
@dataclass
class ImageFormat:
    """Image format configuration"""
    name: str
    extension: str
    mime_type: str
    quality: int
    optimize: bool

class ImagePipeline:
    """Advanced image processing pipeline with optimization, resizing, and format conversion"""
    
    def __init__(self):
        # Supported formats
        self.supported_formats = {
            "JPEG": ImageFormat("JPEG", "jpg", "image/jpeg", 85, True),
            "PNG": ImageFormat("PNG", "png", "image/png", 9, True),
            "WEBP": ImageFormat("WEBP", "webp", "image/webp", 80, True),
            "AVIF": ImageFormat("AVIF", "avif", "image/avif", 50, True)
        }
        
        # Preset dimensions for different use cases
        self.presets = {
            "thumbnail": ImageDimensions(400, 400),
            "medium": ImageDimensions(800, 800),
            "large": ImageDimensions(1200, 1200),
            "hero": ImageDimensions(1920, 1080),
            "social": ImageDimensions(1080, 1080),
            "print": ImageDimensions(3000, 3000)
        }
        
        # Maximum file sizes (in bytes)
        self.max_file_sizes = {
            "thumbnail": 50000,      # 50KB
            "medium": 200000,        # 200KB
            "large": 500000,         # 500KB
            "hero": 1000000,         # 1MB
            "social": 500000,        # 500KB
            "print": 5000000         # 5MB
        }
    
    def generate_image_hash(self, image_data: bytes) -> str:
        """Generate SHA-256 hash of image data for deduplication"""
        return hashlib.sha256(image_data).hexdigest()
    
    def validate_image(self, image_data: bytes, filename: str) -> Dict[str, Any]:
        """Validate image for security and compatibility"""
        try:
            # Check file size
            if len(image_data) > 50 * 1024 * 1024:  # 50MB limit
                return {"valid": False, "error": "File too large (max 50MB)"}
            
            # Check file signature
            image_signatures = {
                b'\x89PNG\r\n\x1a\n': 'PNG',
                b'\xff\xd8\xff': 'JPEG',
                b'RIFF': 'WEBP',
                b'\x00\x00\x00 ftypavif': 'AVIF'
            }
            
            detected_format = None
            for signature, format_name in image_signatures.items():
                if image_data.startswith(signature):
                    detected_format = format_name
                    break
            
            if not detected_format:
                return {"valid": False, "error": "Unsupported image format"}
            
            # Try to open with PIL
            with Image.open(io.BytesIO(image_data)) as img:
                # Check for image bombs
                if img.width > 10000 or img.height > 10000:
                    return {"valid": False, "error": "Image dimensions too large"}
                
                # Check for suspicious metadata
                if hasattr(img, 'text') and img.text:
                    dangerous_keywords = ['<script', 'javascript:', 'vbscript:']
                    for key, value in (img.text or {}).items():
                        if isinstance(value, str):
                            for keyword in dangerous_keywords:
                                if keyword.lower() in value.lower():
                                    return {"valid": False, "error": "Suspicious metadata detected"}
                
                return {
                    "valid": True,
                    "format": detected_format,
                    "width": img.width,
                    "height": img.height,
                    "mode": img.mode,
                    "size_bytes": len(image_data)
                }
                
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "validate_image", "filename": filename})
            return {"valid": False, "error": f"Invalid image: {str(e)}"}
    
    def convert_color_mode(self, img: Image.Image, target_format: str) -> Image.Image:
        """Convert image color mode based on target format"""
        if target_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            # JPEG doesn't support transparency, convert to RGB
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            if img.mode in ("RGBA", "LA"):
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            return background
        elif target_format == "WEBP" and img.mode == "P":
            return img.convert("RGBA")
        elif target_format == "PNG" and img.mode not in ("RGBA", "RGB", "L"):
            return img.convert("RGBA")
        else:
            return img
    
    def resize_image(
        self, 
        img: Image.Image, 
        target_width: int, 
        target_height: int,
        maintain_aspect_ratio: bool = True,
        crop_to_fit: bool = False
    ) -> Image.Image:
        """Resize image with smart cropping and aspect ratio preservation"""
        original_width, original_height = img.size
        
        if maintain_aspect_ratio and not crop_to_fit:
            # Calculate new dimensions maintaining aspect ratio
            ratio = min(target_width / original_width, target_height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            
            # Resize and then pad to exact dimensions
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create background and center the image
            background = Image.new("RGB", (target_width, target_height), (255, 255, 255))
            offset_x = (target_width - new_width) // 2
            offset_y = (target_height - new_height) // 2
            background.paste(resized_img, (offset_x, offset_y))
            
            return background
        
        elif crop_to_fit:
            # Crop to fill the target dimensions
            ratio = max(target_width / original_width, target_height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Crop to exact dimensions
            left = (new_width - target_width) // 2
            top = (new_height - target_height) // 2
            right = left + target_width
            bottom = top + target_height
            
            return resized_img.crop((left, top, right, bottom))
        
        else:
            # Simple resize without maintaining aspect ratio
            return img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    def enhance_image(self, img: Image.Image, enhancements: Dict[str, float]) -> Image.Image:
        """Apply image enhancements"""
        enhanced_img = img.copy()
        
        # Brightness
        if "brightness" in enhancements:
            enhancer = ImageEnhance.Brightness(enhanced_img)
            enhanced_img = enhancer.enhance(enhancements["brightness"])
        
        # Contrast
        if "contrast" in enhancements:
            enhancer = ImageEnhance.Contrast(enhanced_img)
            enhanced_img = enhancer.enhance(enhancements["contrast"])
        
        # Sharpness
        if "sharpness" in enhancements:
            enhancer = ImageEnhance.Sharpness(enhanced_img)
            enhanced_img = enhancer.enhance(enhancements["sharpness"])
        
        # Color saturation
        if "saturation" in enhancements:
            enhancer = ImageEnhance.Color(enhanced_img)
            enhanced_img = enhancer.enhance(enhancements["saturation"])
        
        return enhanced_img
    
    def apply_filters(self, img: Image.Image, filters: List[str]) -> Image.Image:
        """Apply artistic filters to image"""
        filtered_img = img.copy()
        
        for filter_name in filters:
            if filter_name == "blur":
                filtered_img = filtered_img.filter(ImageFilter.GaussianBlur(radius=2))
            elif filter_name == "sharpen":
                filtered_img = filtered_img.filter(ImageFilter.SHARPEN)
            elif filter_name == "edge_enhance":
                filtered_img = filtered_img.filter(ImageFilter.EDGE_ENHANCE)
            elif filter_name == "smooth":
                filtered_img = filtered_img.filter(ImageFilter.SMOOTH)
            elif filter_name == "emboss":
                filtered_img = filtered_img.filter(ImageFilter.EMBOSS)
        
        return filtered_img
    
    def save_image(
        self, 
        img: Image.Image, 
        format_config: ImageFormat,
        quality: Optional[int] = None
    ) -> bytes:
        """Save image to bytes with specified format and quality"""
        output = io.BytesIO()
        
        save_kwargs = {"format": format_config.name}
        
        if format_config.name == "JPEG":
            save_kwargs["quality"] = quality or format_config.quality
            save_kwargs["optimize"] = format_config.optimize
        elif format_config.name == "WEBP":
            save_kwargs["quality"] = quality or format_config.quality
            save_kwargs["optimize"] = format_config.optimize
            save_kwargs["method"] = 6  # Better compression
        elif format_config.name == "PNG":
            save_kwargs["optimize"] = format_config.optimize
            save_kwargs["compress_level"] = 6
        
        img.save(output, **save_kwargs)
        return output.getvalue()
    
    async def process_image(
        self,
        image_data: bytes,
        filename: str,
        presets: List[str] = None,
        formats: List[str] = None,
        enhancements: Dict[str, float] = None,
        filters: List[str] = None
    ) -> Dict[str, Any]:
        """Process image through the complete pipeline"""
        try:
            # Validate image
            validation_result = self.validate_image(image_data, filename)
            if not validation_result["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=validation_result["error"]
                )
            
            # Open image
            with Image.open(io.BytesIO(image_data)) as img:
                original_img = img.copy()
                
                # Apply enhancements if specified
                if enhancements:
                    img = self.enhance_image(img, enhancements)
                
                # Apply filters if specified
                if filters:
                    img = self.apply_filters(img, filters)
                
                # Generate image hash
                image_hash = self.generate_image_hash(image_data)
                
                # Process presets
                presets = presets or ["medium", "thumbnail"]
                formats = formats or ["WEBP", "JPEG"]
                
                processed_images = {}
                
                for preset_name in presets:
                    if preset_name not in self.presets:
                        continue
                    
                    target_dims = self.presets[preset_name]
                    
                    for format_name in formats:
                        if format_name not in self.supported_formats:
                            continue
                        
                        format_config = self.supported_formats[format_name]
                        
                        # Convert color mode
                        processed_img = self.convert_color_mode(img, format_config.name)
                        
                        # Resize
                        processed_img = self.resize_image(
                            processed_img,
                            target_dims.width,
                            target_dims.height,
                            maintain_aspect_ratio=True,
                            crop_to_fit=False
                        )
                        
                        # Save
                        processed_bytes = self.save_image(processed_img, format_config)
                        
                        # Check file size
                        max_size = self.max_file_sizes.get(preset_name, 1000000)
                        if len(processed_bytes) > max_size:
                            # Reduce quality and try again
                            reduced_quality = max(format_config.quality - 20, 30)
                            processed_bytes = self.save_image(processed_img, format_config, reduced_quality)
                        
                        # Store result
                        key = f"{preset_name}_{format_name.lower()}"
                        processed_images[key] = {
                            "data": processed_bytes,
                            "width": target_dims.width,
                            "height": target_dims.height,
                            "format": format_config.name,
                            "size_bytes": len(processed_bytes),
                            "mime_type": format_config.mime_type
                        }
                
                return {
                    "success": True,
                    "image_hash": image_hash,
                    "original_info": validation_result,
                    "processed_images": processed_images
                }
                
        except HTTPException:
            raise
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "process_image",
                "filename": filename,
                "presets": presets,
                "formats": formats
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Image processing failed: {str(e)}"
            )
    
    async def upload_processed_images(
        self,
        processed_images: Dict[str, Any],
        base_filename: str,
        folder: str = "processed"
    ) -> Dict[str, str]:
        """Upload processed images to S3"""
        upload_urls = {}
        
        for key, image_data in processed_images.items():
            try:
                # Generate filename
                extension = image_data["format"].lower()
                filename = f"{folder}/{base_filename}_{key}.{extension}"
                
                # Upload to S3
                url = await s3_storage._upload_to_s3(
                    content=image_data["data"],
                    key=filename,
                    content_type=image_data["mime_type"]
                )
                
                upload_urls[key] = url
                
            except Exception as e:
                sentry_manager.capture_exception(e, {
                    "action": "upload_processed_image",
                    "key": key,
                    "filename": base_filename
                })
                # Continue with other images even if one fails
                continue
        
        return upload_urls
    
    async def create_image_variants(
        self,
        image_data: bytes,
        filename: str,
        design_id: str
    ) -> Dict[str, Any]:
        """Create all necessary image variants for a design"""
        try:
            # Process image with standard presets
            result = await self.process_image(
                image_data=image_data,
                filename=filename,
                presets=["thumbnail", "medium", "large", "social"],
                formats=["WEBP", "JPEG"],
                enhancements={"brightness": 1.0, "contrast": 1.0}
            )
            
            if not result["success"]:
                return result
            
            # Generate base filename
            base_filename = f"design_{design_id}"
            
            # Upload to S3
            upload_urls = await self.upload_processed_images(
                result["processed_images"],
                base_filename,
                folder="designs"
            )
            
            return {
                "success": True,
                "image_hash": result["image_hash"],
                "variants": upload_urls,
                "original_info": result["original_info"]
            }
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "create_image_variants",
                "design_id": design_id
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create image variants: {str(e)}"
            )

# Global image pipeline instance
image_pipeline = ImagePipeline()
