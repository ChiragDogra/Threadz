# Threadz Production Deployment Guide

## 🚀 Production Blockers Implementation Status

### ✅ **Completed Tasks (Weeks 1-4)**

#### 1. **SQLite → PostgreSQL Migration + Alembic Setup**
- ✅ Updated `requirements.txt` with PostgreSQL dependencies
- ✅ Enhanced `database.py` with asyncpg support and connection pooling
- ✅ Complete Alembic configuration with migration scripts
- ✅ Environment-based database URL configuration
- ✅ Production-ready database connection management

#### 2. **Real Payment Gateway Integration (Razorpay)**
- ✅ Complete Razorpay service implementation (`payment.py`)
- ✅ Real order creation with Razorpay integration
- ✅ Payment signature verification
- ✅ Webhook handling for payment events
- ✅ Enhanced order management with payment status tracking
- ✅ Error handling and security measures

#### 3. **HTTPS/SSL Certificates Configuration**
- ✅ Security middleware with comprehensive headers
- ✅ SSL context configuration for development and production
- ✅ Self-signed certificate generation script
- ✅ HTTPS redirect middleware
- ✅ Trusted hosts configuration
- ✅ Content Security Policy implementation

#### 4. **Proper Secrets Management**
- ✅ Comprehensive settings management (`config.py`)
- ✅ Environment variable validation
- ✅ Production and development environment configs
- ✅ Secret validation on startup
- ✅ Pydantic-based configuration with validation

#### 5. **Sentry Error Tracking**
- ✅ Complete Sentry integration (`sentry_config.py`)
- ✅ Error filtering and data sanitization
- ✅ Custom context management
- ✅ Operation tracking decorators and context managers
- ✅ Global exception handler integration
- ✅ Performance monitoring setup

#### 6. **Cloud Deployment with Auto-scaling**
- ✅ Docker containerization (multi-stage builds)
- ✅ Docker Compose for local development
- ✅ Kubernetes deployment manifests
- ✅ Horizontal Pod Autoscaler configuration
- ✅ Ingress with SSL/TLS termination
- ✅ Load balancing and rate limiting
- ✅ Automated deployment script
- ✅ Health checks and monitoring

---

## 📋 **Deployment Instructions**

### Prerequisites
1. **Docker & Docker Compose**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Kubernetes Cluster**
   - EKS, GKE, or AKS cluster
   - kubectl configured
   - Helm 3 installed

3. **Environment Variables**
   ```bash
   # Copy production template
   cp backend/.env.production .env
   
   # Fill in your actual values
   nano .env
   ```

### Quick Deployment

#### Option 1: Docker Compose (Development/Staging)
```bash
# Set environment variables
export POSTGRES_PASSWORD=your_secure_password
export SECRET_KEY=your_32_character_secret_key
export RAZORPAY_KEY_ID=your_razorpay_key
export RAZORPAY_KEY_SECRET=your_razorpay_secret

# Deploy with Docker Compose
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Check status
docker-compose ps
```

#### Option 2: Kubernetes (Production)
```bash
# Set environment variables
export DOCKER_REGISTRY=your-registry.com
export DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
export SECRET_KEY=your_production_secret_key

# Deploy to Kubernetes
./deploy.sh deploy

# Verify deployment
kubectl get pods -n threadz
kubectl get ingress -n threadz
```

### SSL Certificate Setup

#### Development (Self-signed)
```bash
# Generate certificates
cd backend
./generate_ssl_cert.sh

# Use generated certificates
export SSL_CERT_PATH=./ssl/localhost.crt
export SSL_KEY_PATH=./ssl/localhost.key
```

#### Production (Let's Encrypt)
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificates
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Update nginx.conf with certificate paths
```

### Database Migration

#### Initial Setup
```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

#### Production Migration
```bash
# Backup database first
pg_dump threadz_db > backup.sql

# Run migration
alembic upgrade head

# Verify migration
alembic current
```

### Monitoring and Logging

#### Sentry Setup
1. Create Sentry account
2. Create new project
3. Set `SENTRY_DSN` environment variable
4. Error tracking will be automatically enabled

#### Health Checks
```bash
# Application health
curl https://yourdomain.com/health

# Kubernetes health
kubectl get pods -n threadz
kubectl logs -f deployment/threadz-backend -n threadz
```

---

## 🔧 **Configuration Files**

### Environment Variables
| Variable | Description | Required |
|----------|-------------|-----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `SECRET_KEY` | JWT signing key (32+ chars) | ✅ |
| `RAZORPAY_KEY_ID` | Razorpay API key | ✅ |
| `RAZORPAY_KEY_SECRET` | Razorpay secret | ✅ |
| `SENTRY_DSN` | Sentry error tracking | ✅ |
| `ALLOWED_ORIGINS` | CORS allowed origins | ✅ |
| `SSL_CERT_PATH` | SSL certificate path | ✅ |
| `SSL_KEY_PATH` | SSL private key path | ✅ |

### Kubernetes Resources
- **Deployments**: Backend (3 replicas), Frontend (2 replicas)
- **Services**: Internal cluster communication
- **Ingress**: External access with SSL termination
- **HPA**: Auto-scaling based on CPU/memory
- **Secrets**: Encrypted configuration storage

---

## 📊 **Auto-scaling Configuration**

### Horizontal Pod Autoscaler
- **Backend**: 3-10 replicas
  - CPU target: 70%
  - Memory target: 80%
  - Scale up: 100% or 4 pods per 15s
  - Scale down: 10% per minute

- **Frontend**: 2-6 replicas
  - CPU target: 70%
  - Memory target: 80%
  - Scale up: 100% or 2 pods per 15s
  - Scale down: 10% per minute

### Resource Limits
- **Backend Pod**: 512Mi memory, 500m CPU
- **Frontend Pod**: 256Mi memory, 200m CPU

---

## 🔒 **Security Measures**

### Implemented Security Features
1. **Authentication**: JWT with secure secret keys
2. **Authorization**: User-specific data access
3. **Input Validation**: Comprehensive input sanitization
4. **File Upload**: Type validation, size limits, secure filenames
5. **Rate Limiting**: IP-based request throttling
6. **SSL/TLS**: HTTPS enforcement with modern ciphers
7. **Security Headers**: CSP, HSTS, XSS protection
8. **Error Tracking**: Sentry integration with data filtering

### Security Headers
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'...
```

---

## 🚨 **Troubleshooting**

### Common Issues

#### Database Connection Errors
```bash
# Check database pod
kubectl get pods -n threadz | grep postgres

# Check database logs
kubectl logs -f deployment/postgres -n threadz

# Test connection
kubectl exec -it deployment/threadz-backend -n threadz -- python -c "from app.database import engine; print('Connected')"
```

#### SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in /path/to/cert.crt -text -noout

# Test SSL connection
openssl s_client -connect yourdomain.com:443

# Renew certificates
sudo certbot renew
```

#### Payment Gateway Issues
```bash
# Check Razorpay credentials
curl -X POST https://api.razorpay.com/v1/orders \
  -u your_key_id:your_key_secret \
  -d '{"amount":50000,"currency":"INR","receipt":"test"}'

# Check webhook logs
kubectl logs -f deployment/threadz-backend -n threadz | grep webhook
```

### Performance Issues
```bash
# Check resource usage
kubectl top pods -n threadz

# Check HPA status
kubectl get hpa -n threadz

# Scale manually if needed
kubectl scale deployment threadz-backend --replicas=5 -n threadz
```

---

## 📈 **Monitoring and Alerting**

### Metrics to Monitor
1. **Application Metrics**
   - Response time
   - Error rate
   - Request rate
   - Active users

2. **Infrastructure Metrics**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network traffic

3. **Business Metrics**
   - Order conversion rate
   - Payment success rate
   - Design upload rate
   - User engagement

### Alerting Setup
- **Sentry**: Error tracking and alerting
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and alerting
- **Kubernetes**: Pod and node health

---

## 🔄 **CI/CD Pipeline**

### GitHub Actions Workflow
```yaml
name: Deploy to Production
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Kubernetes
        run: |
          ./deploy.sh deploy
        env:
          DOCKER_REGISTRY: ${{ secrets.DOCKER_REGISTRY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
```

---

## 📞 **Support and Maintenance**

### Regular Maintenance Tasks
1. **Daily**: Monitor error rates and performance
2. **Weekly**: Review security logs and update dependencies
3. **Monthly**: Database maintenance and backup verification
4. **Quarterly**: Security audit and performance optimization

### Emergency Procedures
1. **Service Outage**: Check pod status, restart if needed
2. **Database Issues**: Switch to read replica, investigate logs
3. **Security Incident**: Rotate secrets, review access logs
4. **Performance Degradation**: Scale up resources, investigate bottlenecks

---

## 🎯 **Next Steps**

After completing these production blockers, the application is ready for production deployment with:

- ✅ **Scalable Architecture**: Auto-scaling based on load
- ✅ **Secure Payment Processing**: Real Razorpay integration
- ✅ **Robust Database**: PostgreSQL with migrations
- ✅ **SSL/TLS Security**: HTTPS with modern security
- ✅ **Error Monitoring**: Sentry integration
- ✅ **Secrets Management**: Environment-based configuration
- ✅ **Container Orchestration**: Kubernetes deployment
- ✅ **CI/CD Ready**: Automated deployment pipeline

The application is now production-ready with enterprise-grade security, scalability, and monitoring capabilities.
