# Threadz - Custom Fashion Platform

A full-stack web application that allows users to create custom clothing designs through three pathways: uploading their own artwork, exploring community designs, or generating designs with AI.

## 🎨 Features

- **Upload Designs**: Upload your own artwork and preview it on various garments
- **Explore Community**: Browse and discover designs created by other users
- **AI Generation**: Generate unique designs using AI (Premium feature)
- **Product Catalog**: Browse different clothing types (t-shirts, hoodies, jackets)
- **Shopping Cart**: Add custom designs to products and manage cart
- **Order Management**: Complete checkout process with Razorpay integration
- **User Authentication**: Secure JWT-based authentication system

## 🏗️ Architecture

### Backend (FastAPI + SQLAlchemy)
- **Framework**: FastAPI with async support
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT tokens with bcrypt password hashing
- **File Storage**: Local file system for design uploads
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

### Frontend (Next.js + TypeScript)
- **Framework**: Next.js 16 with App Router
- **UI**: Tailwind CSS with shadcn/ui components
- **State Management**: Redux Toolkit
- **Canvas**: Fabric.js for design manipulation
- **3D Visualization**: Three.js for product previews

## 📁 Project Structure

```
Threadz-V1/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── database.py          # Database configuration
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── designs.py           # Design management endpoints
│   │   ├── products.py          # Product catalog endpoints
│   │   ├── orders.py            # Order management endpoints
│   │   └── schemas*.py          # Pydantic schemas
│   ├── requirements.txt         # Python dependencies
│   ├── uploads/                 # File storage directory
│   └── venv/                    # Virtual environment
└── frontend/
    ├── src/
    │   ├── app/                 # Next.js app router pages
    │   ├── components/          # React components
    │   ├── store/               # Redux store configuration
    │   └── lib/                 # Utility functions
    ├── package.json             # Node.js dependencies
    └── public/                  # Static assets
```

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.13+
- Git

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd Threadz-V1/backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd Threadz-V1/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:3000`

## 📊 Database Schema

### Users
- User authentication and profile information
- Addresses for shipping

### Designs
- Uploaded, AI-generated, or community designs
- Image storage and metadata
- Moderation status

### Products
- Clothing catalog (t-shirts, hoodies, etc.)
- Variants (colors, sizes)
- Pricing information

### Orders
- Order management
- Integration with payment system
- Order items linking designs to products

## 🔐 Authentication

The application uses JWT-based authentication:
- **Registration**: Email/password with optional phone
- **Login**: Returns JWT token with user info
- **Protected Routes**: Design upload, order management require authentication

## 🎯 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login

### Designs
- `POST /api/v1/designs/upload` - Upload design (protected)
- `GET /api/v1/designs/explore` - Browse public designs
- `POST /api/v1/designs/ai-generate` - Generate AI design (protected)

### Products
- `GET /api/v1/products/` - List all products
- `GET /api/v1/products/{product_id}` - Get product details

### Orders
- `POST /api/v1/orders/` - Create order (protected)
- `POST /api/v1/orders/verify` - Verify payment (protected)
- `GET /api/v1/orders/my-orders` - Get user orders (protected)

## 🛠️ Development

### Environment Variables
Create `.env` files in both backend and frontend directories:

**Backend (.env)**
```
DATABASE_URL=sqlite+aiosqlite:///./sql_app.db
SECRET_KEY=your-secret-key-here
```

**Frontend (.env.local)**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Code Style
- **Backend**: Python with async/await patterns
- **Frontend**: TypeScript with strict typing
- **UI Components**: shadcn/ui design system
- **State Management**: Redux Toolkit with proper typing

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📦 Deployment

### Backend Production
1. Use PostgreSQL instead of SQLite
2. Set up proper file storage (AWS S3, etc.)
3. Configure environment variables
4. Use production ASGI server (Gunicorn + Uvicorn)

### Frontend Production
1. Build the application: `npm run build`
2. Deploy to Vercel, Netlify, or similar platform
3. Configure environment variables

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the code comments for additional context

---

**Built with ❤️ using FastAPI, Next.js, and modern web technologies**
