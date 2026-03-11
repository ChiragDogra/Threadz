"""
Advanced Search and Filtering System for Threadz Application
"""
import re
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, and_, or_, desc, asc, text
from fastapi import HTTPException, status, Query
from pydantic import BaseModel

from . import models
from .security_hardening import validate_secure_input
from .sentry_config import sentry_manager

class SearchService:
    """Advanced search service with filtering, sorting, and ranking"""
    
    def __init__(self):
        self.min_search_length = 2
        self.max_search_length = 100
        
        # Search weights for different fields
        self.search_weights = {
            "design_name": 3.0,
            "tags": 2.5,
            "description": 2.0,
            "user_name": 1.5,
            "category": 1.0
        }
    
    def validate_search_query(self, query: str) -> bool:
        """Validate search query for security and length"""
        if not query:
            return False
        
        query = query.strip()
        
        # Length validation
        if len(query) < self.min_search_length or len(query) > self.max_search_length:
            return False
        
        # Security validation
        dangerous_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'eval\s*\(',
            r'exec\s*\('
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False
        
        return True
    
    def preprocess_search_query(self, query: str) -> str:
        """Preprocess search query for better matching"""
        query = query.strip()
        
        # Remove special characters but keep spaces and basic punctuation
        query = re.sub(r'[^\w\s\-_.,]', ' ', query)
        
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query)
        
        return query.lower()
    
    async def search_designs(
        self,
        db: AsyncSession,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        design_source: Optional[str] = None,
        is_public: Optional[bool] = None,
        sort_by: str = "relevance",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[models.Design], int]:
        """Search designs with advanced filtering and ranking"""
        try:
            # Base query
            search_query = select(models.Design).options(selectinload(models.Design.user))
            count_query = select(func.count(models.Design.design_id))
            
            # Apply filters
            filters = []
            
            # Text search
            if query:
                if not self.validate_search_query(query):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid search query"
                    )
                
                processed_query = self.preprocess_search_query(query)
                
                # Create search conditions with weights
                search_conditions = []
                
                # Design name (highest weight)
                search_conditions.append(
                    models.Design.design_name.ilike(f"%{processed_query}%")
                )
                
                # Tags
                if hasattr(models.Design, 'tags') and models.Design.tags:
                    search_conditions.append(
                        models.Design.tags.ilike(f"%{processed_query}%")
                    )
                
                # User name
                search_conditions.append(
                    models.User.full_name.ilike(f"%{processed_query}%")
                )
                
                # Category
                if hasattr(models.Design, 'category') and models.Design.category:
                    search_conditions.append(
                        models.Design.category.ilike(f"%{processed_query}%")
                    )
                
                if search_conditions:
                    filters.append(or_(*search_conditions))
            
            # Category filter
            if category:
                filters.append(models.Design.category == validate_secure_input(category))
            
            # Tags filter
            if tags and isinstance(tags, list):
                tag_conditions = []
                for tag in tags:
                    safe_tag = validate_secure_input(tag)
                    if hasattr(models.Design, 'tags'):
                        tag_conditions.append(models.Design.tags.ilike(f"%{safe_tag}%"))
                
                if tag_conditions:
                    filters.append(and_(*tag_conditions))
            
            # Design source filter
            if design_source:
                filters.append(models.Design.design_source == design_source)
            
            # Public/private filter
            if is_public is not None:
                filters.append(models.Design.is_public == is_public)
            
            # Apply filters to queries
            if filters:
                search_query = search_query.where(and_(*filters))
                count_query = count_query.where(and_(*filters))
            
            # Apply sorting
            if sort_by == "relevance" and query:
                # Custom relevance scoring (simplified - would use full-text search in production)
                search_query = search_query.order_by(
                    desc(models.Design.created_at)  # Fallback to created_at
                )
            elif sort_by == "created_at":
                if sort_order == "desc":
                    search_query = search_query.order_by(desc(models.Design.created_at))
                else:
                    search_query = search_query.order_by(asc(models.Design.created_at))
            elif sort_by == "name":
                if sort_order == "desc":
                    search_query = search_query.order_by(desc(models.Design.design_name))
                else:
                    search_query = search_query.order_by(asc(models.Design.design_name))
            elif sort_by == "popularity":
                # Sort by view count or likes (would need to add these fields)
                search_query = search_query.order_by(desc(models.Design.created_at))
            else:
                # Default sorting
                search_query = search_query.order_by(desc(models.Design.created_at))
            
            # Apply pagination
            search_query = search_query.offset(skip).limit(limit)
            
            # Execute queries
            result = await db.execute(search_query)
            designs = result.scalars().all()
            
            count_result = await db.execute(count_query)
            total_count = count_result.scalar() or 0
            
            return designs, total_count
            
        except HTTPException:
            raise
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "search_designs",
                "query": query[:50] if query else None
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Search failed"
            )
    
    async def search_products(
        self,
        db: AsyncSession,
        query: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: Optional[bool] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[models.Product], int]:
        """Search products with filtering"""
        try:
            # Base query
            search_query = select(models.Product).options(
                selectinload(models.Product.variants)
            )
            count_query = select(func.count(models.Product.product_id))
            
            # Apply filters
            filters = []
            
            # Text search
            if query:
                if not self.validate_search_query(query):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid search query"
                    )
                
                processed_query = self.preprocess_search_query(query)
                
                search_conditions = [
                    models.Product.product_name.ilike(f"%{processed_query}%"),
                    models.Product.description.ilike(f"%{processed_query}%"),
                    models.Product.category.ilike(f"%{processed_query}%")
                ]
                
                filters.append(or_(*search_conditions))
            
            # Category filter
            if category:
                filters.append(models.Product.category == validate_secure_input(category))
            
            # Price range filter
            if min_price is not None:
                filters.append(models.Product.base_price >= min_price)
            
            if max_price is not None:
                filters.append(models.Product.base_price <= max_price)
            
            # Stock filter
            if in_stock is not None:
                # Would need to join with variants and check stock
                pass
            
            # Apply filters to queries
            if filters:
                search_query = search_query.where(and_(*filters))
                count_query = count_query.where(and_(*filters))
            
            # Apply sorting
            if sort_by == "name":
                if sort_order == "desc":
                    search_query = search_query.order_by(desc(models.Product.product_name))
                else:
                    search_query = search_query.order_by(asc(models.Product.product_name))
            elif sort_by == "price":
                if sort_order == "desc":
                    search_query = search_query.order_by(desc(models.Product.base_price))
                else:
                    search_query = search_query.order_by(asc(models.Product.base_price))
            elif sort_by == "created_at":
                if sort_order == "desc":
                    search_query = search_query.order_by(desc(models.Product.created_at))
                else:
                    search_query = search_query.order_by(asc(models.Product.created_at))
            else:
                search_query = search_query.order_by(asc(models.Product.product_name))
            
            # Apply pagination
            search_query = search_query.offset(skip).limit(limit)
            
            # Execute queries
            result = await db.execute(search_query)
            products = result.scalars().all()
            
            count_result = await db.execute(count_query)
            total_count = count_result.scalar() or 0
            
            return products, total_count
            
        except HTTPException:
            raise
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "search_products",
                "query": query[:50] if query else None
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Product search failed"
            )
    
    async def get_search_suggestions(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 10
    ) -> Dict[str, List[str]]:
        """Get search suggestions for autocomplete"""
        try:
            if not self.validate_search_query(query):
                return {"suggestions": []}
            
            processed_query = self.preprocess_search_query(query)
            
            suggestions = []
            
            # Design name suggestions
            design_query = select(models.Design.design_name).where(
                models.Design.design_name.ilike(f"%{processed_query}%"),
                models.Design.is_public == True
            ).limit(limit)
            
            design_result = await db.execute(design_query)
            design_names = [row[0] for row in design_result if row[0]]
            suggestions.extend(design_names)
            
            # Category suggestions
            category_query = select(models.Design.category).where(
                models.Design.category.ilike(f"%{processed_query}%"),
                models.Design.is_public == True
            ).distinct().limit(limit // 2)
            
            category_result = await db.execute(category_query)
            categories = [row[0] for row in category_result if row[0]]
            suggestions.extend(categories)
            
            # Product name suggestions
            product_query = select(models.Product.product_name).where(
                models.Product.product_name.ilike(f"%{processed_query}%")
            ).limit(limit // 2)
            
            product_result = await db.execute(product_query)
            product_names = [row[0] for row in product_result if row[0]]
            suggestions.extend(product_names)
            
            # Remove duplicates and limit
            unique_suggestions = list(set(suggestions))[:limit]
            
            return {"suggestions": unique_suggestions}
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "get_search_suggestions",
                "query": query[:50]
            })
            return {"suggestions": []}
    
    async def get_popular_searches(
        self,
        db: AsyncSession,
        limit: int = 10
    ) -> Dict[str, List[str]]:
        """Get popular search terms (would implement search analytics in production)"""
        try:
            # Mock implementation - would track search analytics in production
            popular_terms = [
                "t-shirt design",
                "custom hoodie",
                "phone case",
                "poster design",
                "logo design",
                "wall art",
                "custom mug",
                "tote bag",
                "sticker design",
                "canvas print"
            ]
            
            return {"popular_searches": popular_terms[:limit]}
            
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "get_popular_searches"})
            return {"popular_searches": []}
    
    async def get_filter_options(
        self,
        db: AsyncSession
    ) -> Dict[str, List[str]]:
        """Get available filter options"""
        try:
            # Get categories
            category_query = select(models.Design.category).where(
                models.Design.category.isnot(None)
            ).distinct()
            category_result = await db.execute(category_query)
            categories = [row[0] for row in category_result if row[0]]
            
            # Get design sources
            source_query = select(models.Design.design_source).distinct()
            source_result = await db.execute(source_query)
            design_sources = [row[0] for row in source_result if row[0]]
            
            # Get product categories
            product_category_query = select(models.Product.category).where(
                models.Product.category.isnot(None)
            ).distinct()
            product_category_result = await db.execute(product_category_query)
            product_categories = [row[0] for row in product_category_result if row[0]]
            
            return {
                "design_categories": sorted(categories),
                "design_sources": sorted(design_sources),
                "product_categories": sorted(product_categories)
            }
            
        except Exception as e:
            sentry_manager.capture_exception(e, {"action": "get_filter_options"})
            return {
                "design_categories": [],
                "design_sources": [],
                "product_categories": []
            }

# Global search service instance
search_service = SearchService()
