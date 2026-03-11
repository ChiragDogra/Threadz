#!/bin/bash

# Threadz Production Deployment Script
# This script handles the complete deployment process

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
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        log_error "Helm is not installed"
        exit 1
    fi
    
    # Check if environment variables are set
    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL environment variable is not set"
        exit 1
    fi
    
    if [ -z "$SECRET_KEY" ]; then
        log_error "SECRET_KEY environment variable is not set"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build and push Docker images
build_and_push_images() {
    log_info "Building and pushing Docker images..."
    
    # Build backend image
    log_info "Building backend image..."
    docker build -t $DOCKER_REGISTRY/$PROJECT_NAME/backend:latest .
    
    # Build frontend image
    log_info "Building frontend image..."
    cd frontend
    docker build -t $DOCKER_REGISTRY/$PROJECT_NAME/frontend:latest .
    cd ..
    
    # Push images
    log_info "Pushing images to registry..."
    docker push $DOCKER_REGISTRY/$PROJECT_NAME/backend:latest
    docker push $DOCKER_REGISTRY/$PROJECT_NAME/frontend:latest
    
    log_success "Images built and pushed successfully"
}

# Deploy to Kubernetes
deploy_to_kubernetes() {
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
        --env="DATABASE_URL=$DATABASE_URL" \
        --command -- alembic upgrade head
    
    # Deploy application
    log_info "Deploying application..."
    kubectl apply -f k8s/deployment.yaml -n $PROJECT_NAME
    kubectl apply -f k8s/service.yaml -n $PROJECT_NAME
    kubectl apply -f k8s/ingress.yaml -n $PROJECT_NAME
    kubectl apply -f k8s/hpa.yaml -n $PROJECT_NAME
    
    log_success "Deployment completed successfully"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Wait for pods to be ready
    kubectl wait --for=condition=available deployment/threadz-backend -n $PROJECT_NAME --timeout=600s
    kubectl wait --for=condition=available deployment/threadz-frontend -n $PROJECT_NAME --timeout=600s
    
    # Check pod status
    kubectl get pods -n $PROJECT_NAME
    
    # Get ingress URL
    INGRESS_URL=$(kubectl get ingress threadz-ingress -n $PROJECT_NAME -o jsonpath='{.spec.rules[0].host}')
    
    log_success "Deployment is ready!"
    log_info "Application URL: https://$INGRESS_URL"
    
    # Health check
    log_info "Performing health check..."
    if curl -f https://$INGRESS_URL/health; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        exit 1
    fi
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."
    
    kubectl rollout undo deployment/threadz-backend -n $PROJECT_NAME
    kubectl rollout undo deployment/threadz-frontend -n $PROJECT_NAME
    
    log_success "Rollback completed"
}

# Main deployment flow
main() {
    log_info "Starting Threadz deployment..."
    
    check_prerequisites
    
    if [ "$1" = "rollback" ]; then
        rollback
        exit 0
    fi
    
    build_and_push_images
    deploy_to_kubernetes
    verify_deployment
    
    log_success "🎉 Threadz deployment completed successfully!"
}

# Handle script arguments
case "$1" in
    "deploy")
        main
        ;;
    "rollback")
        rollback
        ;;
    *)
        echo "Usage: $0 {deploy|rollback}"
        exit 1
        ;;
esac
