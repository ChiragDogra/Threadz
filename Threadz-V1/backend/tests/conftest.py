"""
pytest configuration and fixtures for Threadz backend tests
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.config import settings
from app.auth import create_access_token

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# Test session factory
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database dependency override."""
    
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
    
    # Clean up dependency override
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_data():
    """Test user data for creating test users."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }

@pytest.fixture
async def test_user(db_session: AsyncSession, test_user_data):
    """Create a test user in the database."""
    from app.models import User
    from app.auth import get_password_hash
    
    user = User(
        email=test_user_data["email"],
        password_hash=get_password_hash(test_user_data["password"]),
        full_name=test_user_data["full_name"],
        is_email_verified=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test user."""
    access_token = create_access_token(data={"sub": test_user.user_id})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def test_product_data():
    """Test product data."""
    return {
        "product_name": "Test T-Shirt",
        "description": "A comfortable test t-shirt",
        "category": "t-shirt",
        "base_price": 599,
        "variants": [
            {
                "variant_name": "Small",
                "sku": "TEST-S-S",
                "price": 599,
                "stock": 100,
                "attributes": {"size": "S", "color": "Black"}
            },
            {
                "variant_name": "Medium",
                "sku": "TEST-S-M",
                "price": 599,
                "stock": 100,
                "attributes": {"size": "M", "color": "Black"}
            }
        ]
    }

@pytest.fixture
async def test_product(db_session: AsyncSession, test_product_data):
    """Create a test product in the database."""
    from app.models import Product, ProductVariant
    
    product = Product(
        product_name=test_product_data["product_name"],
        description=test_product_data["description"],
        category=test_product_data["category"],
        base_price=test_product_data["base_price"]
    )
    
    db_session.add(product)
    await db_session.flush()
    
    # Add variants
    for variant_data in test_product_data["variants"]:
        variant = ProductVariant(
            product_id=product.product_id,
            variant_name=variant_data["variant_name"],
            sku=variant_data["sku"],
            price=variant_data["price"],
            stock=variant_data["stock"],
            attributes=variant_data["attributes"]
        )
        db_session.add(variant)
    
    await db_session.commit()
    await db_session.refresh(product)
    
    return product

@pytest.fixture
def test_design_data():
    """Test design data."""
    return {
        "design_name": "Test Design",
        "design_source": "upload",
        "image_url": "https://example.com/test.jpg",
        "thumbnail_url": "https://example.com/test_thumb.jpg",
        "is_public": True,
        "tags": "test,design"
    }

@pytest.fixture
async def test_design(db_session: AsyncSession, test_user, test_design_data):
    """Create a test design in the database."""
    from app.models import Design
    
    design = Design(
        user_id=test_user.user_id,
        design_name=test_design_data["design_name"],
        design_source=test_design_data["design_source"],
        image_url=test_design_data["image_url"],
        thumbnail_url=test_design_data["thumbnail_url"],
        is_public=test_design_data["is_public"],
        tags=test_design_data["tags"],
        width_px=800,
        height_px=800,
        dpi=300
    )
    
    db_session.add(design)
    await db_session.commit()
    await db_session.refresh(design)
    
    return design

@pytest.fixture
def mock_s3_storage(monkeypatch):
    """Mock S3 storage service for testing."""
    from unittest.mock import AsyncMock
    
    mock_storage = AsyncMock()
    mock_storage.upload_design_image.return_value = (
        "https://test-bucket.s3.test-region.amazonaws.com/designs/test.jpg",
        "https://test-bucket.s3.test-region.amazonaws.com/thumbnails/test.jpg"
    )
    mock_storage.upload_ai_generated_image.return_value = (
        "https://test-bucket.s3.test-region.amazonaws.com/ai-designs/test.jpg"
    )
    mock_storage.generate_presigned_url.return_value = (
        "https://test-bucket.s3.test-region.amazonaws.com/designs/test.jpg"
    )
    mock_storage.delete_file.return_value = True
    
    monkeypatch.setattr("app.storage.s3_storage", mock_storage)
    return mock_storage

@pytest.fixture
def mock_ai_service(monkeypatch):
    """Mock AI service for testing."""
    from unittest.mock import AsyncMock
    
    mock_ai = AsyncMock()
    mock_ai.generate_and_upload.return_value = {
        "image_url": "https://test-bucket.s3.test-region.amazonaws.com/ai-designs/test.jpg",
        "thumbnail_url": "https://test-bucket.s3.test-region.amazonaws.com/thumbnails/test.jpg",
        "metadata": {"width": 1024, "height": 1024, "size_bytes": 50000}
    }
    mock_ai.is_available.return_value = True
    
    monkeypatch.setattr("app.ai_service.ai_service", mock_ai)
    return mock_ai

@pytest.fixture
def mock_payment_service(monkeypatch):
    """Mock payment service for testing."""
    from unittest.mock import AsyncMock
    
    mock_payment = AsyncMock()
    mock_payment.create_order.return_value = {
        "id": "order_test123",
        "entity": "order",
        "amount": 59900,
        "currency": "INR",
        "status": "created"
    }
    mock_payment.verify_payment_signature.return_value = True
    
    monkeypatch.setattr("app.payment.razorpay_service", mock_payment)
    return mock_payment

@pytest.fixture
def mock_email_service(monkeypatch):
    """Mock email service for testing."""
    from unittest.mock import AsyncMock
    
    mock_email = AsyncMock()
    mock_email.send_verification_email.return_value = True
    mock_email.send_password_reset_email.return_value = True
    mock_email.is_available.return_value = True
    
    monkeypatch.setattr("app.email.email_service", mock_email)
    return mock_email

@pytest.fixture
def sample_image_bytes():
    """Sample image bytes for file upload tests."""
    # Minimal PNG header for testing
    return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'

@pytest.fixture
def sample_upload_file(sample_image_bytes):
    """Create a sample upload file for testing."""
    from fastapi import UploadFile
    import io
    
    file = UploadFile(
        filename="test.png",
        file=io.BytesIO(sample_image_bytes),
        content_type="image/png"
    )
    return file

# Test configuration
@pytest.fixture(scope="session", autouse=True)
def configure_test_settings():
    """Configure test settings."""
    # Override settings for testing
    original_env = settings.ENVIRONMENT
    settings.ENVIRONMENT = "testing"
    
    yield
    
    # Restore original settings
    settings.ENVIRONMENT = original_env

# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Mark test as unit test")
    config.addinivalue_line("markers", "integration: Mark test as integration test")
    config.addinivalue_line("markers", "slow: Mark test as slow running")
    config.addinivalue_line("markers", "external: Mark test as requiring external services")

# Test utilities
async def create_test_user(db_session: AsyncSession, email: str = "test@example.com") -> "User":
    """Utility to create a test user."""
    from app.models import User
    from app.auth import get_password_hash
    
    user = User(
        email=email,
        password_hash=get_password_hash("TestPassword123!"),
        full_name="Test User",
        is_email_verified=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user

async def create_test_design(db_session: AsyncSession, user_id: str) -> "Design":
    """Utility to create a test design."""
    from app.models import Design
    
    design = Design(
        user_id=user_id,
        design_name="Test Design",
        design_source="upload",
        image_url="https://example.com/test.jpg",
        thumbnail_url="https://example.com/test_thumb.jpg",
        is_public=True,
        tags="test",
        width_px=800,
        height_px=800,
        dpi=300
    )
    
    db_session.add(design)
    await db_session.commit()
    await db_session.refresh(design)
    
    return design

async def create_test_order(db_session: AsyncSession, user_id: str) -> "Order":
    """Utility to create a test order."""
    from app.models import Order, OrderItem, ProductVariant
    
    # Create a test product variant first
    variant = ProductVariant(
        variant_name="Test Variant",
        sku="TEST-001",
        price=599,
        stock=100,
        attributes={"size": "M", "color": "Black"}
    )
    db_session.add(variant)
    await db_session.flush()
    
    # Create order
    order = Order(
        user_id=user_id,
        total_amount=599,
        status="Pending",
        razorpay_order_id="order_test123"
    )
    db_session.add(order)
    await db_session.flush()
    
    # Create order item
    order_item = OrderItem(
        order_id=order.order_id,
        variant_id=variant.variant_id,
        quantity=1,
        unit_price=599
    )
    db_session.add(order_item)
    
    await db_session.commit()
    await db_session.refresh(order)
    
    return order
