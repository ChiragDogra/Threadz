#!/bin/bash

# Threadz Production Deployment Script
# This script handles the complete production deployment process

set -e

# Configuration
DOCKER_REGISTRY="your-registry.com"
PROJECT_NAME="threadz"
ENVIRONMENT="production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if kubectl is installed (for Kubernetes deployment)
    if ! command -v kubectl &> /dev/null; then
        log_warning "kubectl is not installed - Kubernetes deployment will not be available"
    fi
    
    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        log_warning "Helm is not installed - Helm deployment will not be available"
    fi
    
    # Check if environment variables are set
    if [ -z "$POSTGRES_PASSWORD" ]; then
        log_error "POSTGRES_PASSWORD environment variable is not set"
        exit 1
    fi
    
    if [ -z "$SECRET_KEY" ]; then
        log_error "SECRET_KEY environment variable is not set"
        exit 1
    fi
    
    if [ -z "$RAZORPAY_KEY_ID" ]; then
        log_error "RAZORPAY_KEY_ID environment variable is not set"
        exit 1
    fi
    
    # Check SSL certificates
    if [ ! -f "./ssl/cert.pem" ] || [ ! -f "./ssl/key.pem" ]; then
        log_warning "SSL certificates not found in ./ssl/ directory"
        log_info "You can generate self-signed certificates for testing:"
        log_info "  ./backend/generate_ssl_cert.sh"
    fi
    
    log_success "Prerequisites check passed"
}

# Build and push Docker images
build_and_push_images() {
    log_info "Building and pushing Docker images..."
    
    # Build backend image
    log_info "Building backend image..."
    docker build -f Dockerfile.prod -t $DOCKER_REGISTRY/$PROJECT_NAME/backend:latest .
    
    # Build frontend image
    log_info "Building frontend image..."
    cd frontend
    docker build -f Dockerfile.prod -t $DOCKER_REGISTRY/$PROJECT_NAME/frontend:latest .
    cd ..
    
    # Push images if registry is configured
    if [ "$DOCKER_REGISTRY" != "your-registry.com" ]; then
        log_info "Pushing images to registry..."
        docker push $DOCKER_REGISTRY/$PROJECT_NAME/backend:latest
        docker push $DOCKER_REGISTRY/$PROJECT_NAME/frontend:latest
    else
        log_warning "Skipping image push - using local images"
    fi
    
    log_success "Images built successfully"
}

# Deploy with Docker Compose
deploy_docker_compose() {
    log_info "Deploying with Docker Compose..."
    
    # Create environment file
    cat > .env.prod << EOF
# Production Environment Variables
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
SECRET_KEY=$SECRET_KEY
RAZORPAY_KEY_ID=$RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET=$RAZORPAY_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET=$RAZORPAY_WEBHOOK_SECRET
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
AWS_S3_BUCKET=$AWS_S3_BUCKET
AWS_REGION=$AWS_REGION
SENTRY_DSN=$SENTRY_DSN
SENDGRID_API_KEY=$SENDGRID_API_KEY
SENDGRID_FROM_EMAIL=$SENDGRID_FROM_EMAIL
ALLOWED_ORIGINS=$ALLOWED_ORIGINS
NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
EOF
    
    # Stop existing containers
    docker-compose -f docker-compose.prod.yml down
    
    # Start new containers
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log_success "Docker Compose deployment completed successfully"
    else
        log_error "Some services failed to start"
        docker-compose -f docker-compose.prod.yml logs
        exit 1
    fi
}

# Deploy to Kubernetes
deploy_kubernetes() {
    if ! command -v kubectl &> /dev/null; then
        log_warning "kubectl not available - skipping Kubernetes deployment"
        return
    fi
    
    log_info "Deploying to Kubernetes..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace $PROJECT_NAME --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply secrets
    log_info "Creating secrets..."
    kubectl apply -f k8s/secrets.yaml -n $PROJECT_NAME
    
    # Apply configmaps
    log_info "Creating configmaps..."
    kubectl apply -f k8s/configmap.yaml -n $PROJECT_NAME
    
    # Deploy database
    log_info "Deploying PostgreSQL..."
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm upgrade --install postgres bitnami/postgresql \
        --namespace $PROJECT_NAME \
        --set auth.postgresPassword=$POSTGRES_PASSWORD \
        --set auth.database=threadz_db \
        --set primary.persistence.size=20Gi
    
    # Deploy Redis
    log_info "Deploying Redis..."
    helm upgrade --install redis bitnami/redis \
        --namespace $PROJECT_NAME \
        --set auth.password=$REDIS_PASSWORD \
        --set master.persistence.size=10Gi
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgres -n $PROJECT_NAME --timeout=300s
    
    # Run database migrations
    log_info "Running database migrations..."
    kubectl run migration --image=$DOCKER_REGISTRY/$PROJECT_NAME/backend:latest \
        --rm -i --restart=Never -n $PROJECT_NAME \
        --env="DATABASE_URL=postgresql+asyncpg://postgres:$POSTGRES_PASSWORD@postgres:5432/threadz_db" \
        --command -- alembic upgrade head
    
    # Deploy application
    log_info "Deploying application..."
    kubectl apply -f k8s/deployment.yaml -n $PROJECT_NAME
    kubectl apply -f k8s/service.yaml -n $PROJECT_NAME
    kubectl apply -f k8s/ingress.yaml -n $PROJECT_NAME
    kubectl apply -f k8s/hpa.yaml -n $PROJECT_NAME
    
    log_success "Kubernetes deployment completed successfully"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check Docker Compose services
    if docker-compose -f docker-compose.prod.yml ps &> /dev/null; then
        log_info "Checking Docker Compose services..."
        docker-compose -f docker-compose.prod.yml ps
        
        # Health check
        if curl -f http://localhost/health &> /dev/null; then
            log_success "Health check passed"
        else
            log_warning "Health check failed - services may still be starting"
        fi
    fi
    
    # Check Kubernetes services
    if command -v kubectl &> /dev/null; then
        log_info "Checking Kubernetes services..."
        kubectl get pods -n $PROJECT_NAME
        kubectl get services -n $PROJECT_NAME
        kubectl get ingress -n $PROJECT_NAME
        
        # Get ingress URL
        INGRESS_URL=$(kubectl get ingress threadz-ingress -n $PROJECT_NAME -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "")
        
        if [ -n "$INGRESS_URL" ]; then
            log_success "Application URL: https://$INGRESS_URL"
            
            # Health check
            if curl -f https://$INGRESS_URL/health &> /dev/null; then
                log_success "Health check passed"
            else
                log_warning "Health check failed - services may still be starting"
            fi
        fi
    fi
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."
    
    # Docker Compose rollback
    if docker-compose -f docker-compose.prod.yml ps &> /dev/null; then
        log_info "Rolling back Docker Compose deployment..."
        docker-compose -f docker-compose.prod.yml down
        log_info "Docker Compose rollback completed"
    fi
    
    # Kubernetes rollback
    if command -v kubectl &> /dev/null; then
        log_info "Rolling back Kubernetes deployment..."
        kubectl rollout undo deployment/threadz-backend -n $PROJECT_NAME
        kubectl rollout undo deployment/threadz-frontend -n $PROJECT_NAME
        log_success "Kubernetes rollback completed"
    fi
}

# Backup function
backup() {
    log_info "Creating backup..."
    
    # Backup database
    if docker-compose -f docker-compose.prod.yml ps | grep -q "postgres"; then
        log_info "Backing up PostgreSQL database..."
        docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U threadz_user threadz_db > backup_$(date +%Y%m%d_%H%M%S).sql
        log_success "Database backup completed"
    fi
    
    # Backup uploads
    if [ -d "./uploads" ]; then
        log_info "Backing up uploads..."
        tar -czf uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz uploads/
        log_success "Uploads backup completed"
    fi
}

# Show logs
show_logs() {
    log_info "Showing logs..."
    
    # Docker Compose logs
    if docker-compose -f docker-compose.prod.yml ps &> /dev/null; then
        docker-compose -f docker-compose.prod.yml logs -f --tail=100
    fi
    
    # Kubernetes logs
    if command -v kubectl &> /dev/null; then
        kubectl logs -f deployment/threadz-backend -n $PROJECT_NAME --tail=100
    fi
}

# Scale services
scale_services() {
    local service=$1
    local replicas=$2
    
    log_info "Scaling $service to $replicas replicas..."
    
    # Docker Compose scaling
    if docker-compose -f docker-compose.prod.yml ps &> /dev/null; then
        docker-compose -f docker-compose.prod.yml up -d --scale $service=$replicas
    fi
    
    # Kubernetes scaling
    if command -v kubectl &> /dev/null; then
        kubectl scale deployment/$service --replicas=$replicas -n $PROJECT_NAME
    fi
    
    log_success "Scaling completed"
}

# Main deployment flow
main() {
    log_info "Starting Threadz production deployment..."
    
    check_prerequisites
    
    case "$1" in
        "build")
            build_and_push_images
            ;;
        "deploy-compose")
            build_and_push_images
            deploy_docker_compose
            verify_deployment
            ;;
        "deploy-k8s")
            build_and_push_images
            deploy_kubernetes
            verify_deployment
            ;;
        "deploy")
            build_and_push_images
            deploy_docker_compose
            deploy_kubernetes
            verify_deployment
            ;;
        "rollback")
            rollback
            ;;
        "backup")
            backup
            ;;
        "logs")
            show_logs
            ;;
        "scale")
            if [ -z "$2" ] || [ -z "$3" ]; then
                log_error "Usage: $0 scale <service> <replicas>"
                exit 1
            fi
            scale_services $2 $3
            ;;
        *)
            echo "Usage: $0 {build|deploy-compose|deploy-k8s|deploy|rollback|backup|logs|scale <service> <replicas>}"
            exit 1
            ;;
    esac
    
    log_success "🎉 Threadz deployment completed successfully!"
}

# Handle script arguments
case "$1" in
    "help"|"-h"|"--help")
        echo "Threadz Production Deployment Script"
        echo ""
        echo "Usage: $0 [COMMAND] [OPTIONS]"
        echo ""
        echo "Commands:"
        echo "  build           Build Docker images"
        echo "  deploy-compose  Deploy with Docker Compose"
        echo "  deploy-k8s      Deploy to Kubernetes"
        echo "  deploy          Full deployment (Compose + K8s)"
        echo "  rollback        Rollback deployment"
        echo "  backup          Create backup"
        echo "  logs            Show logs"
        echo "  scale           Scale services"
        echo "  help            Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 deploy                    # Full deployment"
        echo "  $0 deploy-compose            # Docker Compose only"
        echo "  $0 scale backend 3            # Scale backend to 3 replicas"
        echo ""
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
