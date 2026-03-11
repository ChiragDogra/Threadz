import React from 'react';
import SkeletonLoader from './skeleton-loader';

interface LoadingStateProps {
  isLoading: boolean;
  error?: string | null;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  errorFallback?: React.ReactNode;
  skeleton?: React.ReactNode;
  className?: string;
}

const LoadingState: React.FC<LoadingStateProps> = ({
  isLoading,
  error,
  children,
  fallback,
  errorFallback,
  skeleton,
  className = ''
}) => {
  if (error) {
    if (errorFallback) {
      return <>{errorFallback}</>;
    }

    return (
      <div className={`flex flex-col items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <div className="mb-4">
            <svg
              className="w-12 h-12 text-red-500 mx-auto"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Something went wrong
          </h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            {error}
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    if (fallback) {
      return <>{fallback}</>;
    }

    if (skeleton) {
      return <>{skeleton}</>;
    }

    return (
      <div className={`space-y-4 ${className}`}>
        <SkeletonLoader variant="text" lines={3} />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="space-y-3">
              <SkeletonLoader variant="rectangular" height={200} />
              <SkeletonLoader variant="text" lines={2} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

// Specific loading components
export const DesignCardSkeleton: React.FC<{ count?: number }> = ({ count = 6 }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {Array.from({ length: count }).map((_, index) => (
      <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
        <SkeletonLoader variant="rectangular" height={250} />
        <div className="p-4 space-y-3">
          <SkeletonLoader variant="text" lines={2} />
          <div className="flex items-center justify-between">
            <SkeletonLoader variant="text" width={100} />
            <SkeletonLoader variant="circular" width={40} height={40} />
          </div>
        </div>
      </div>
    ))}
  </div>
);

export const ProductCardSkeleton: React.FC<{ count?: number }> = ({ count = 4 }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    {Array.from({ length: count }).map((_, index) => (
      <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
        <SkeletonLoader variant="rectangular" height={200} />
        <div className="p-4 space-y-3">
          <SkeletonLoader variant="text" lines={1} />
          <SkeletonLoader variant="text" width={80} />
          <SkeletonLoader variant="text" width={60} />
        </div>
      </div>
    ))}
  </div>
);

export const OrderListSkeleton: React.FC<{ count?: number }> = ({ count = 5 }) => (
  <div className="space-y-4">
    {Array.from({ length: count }).map((_, index) => (
      <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex items-start justify-between space-y-4">
          <div className="flex-1 space-y-3">
            <div className="flex items-center space-x-4">
              <SkeletonLoader variant="text" width={120} />
              <SkeletonLoader variant="text" width={100} />
            </div>
            <SkeletonLoader variant="text" lines={2} />
            <div className="flex items-center space-x-6">
              <SkeletonLoader variant="text" width={80} />
              <SkeletonLoader variant="text" width={80} />
            </div>
          </div>
          <SkeletonLoader variant="rectangular" width={100} height={36} />
        </div>
      </div>
    ))}
  </div>
);

export const UserProfileSkeleton: React.FC = () => (
  <div className="max-w-4xl mx-auto p-6">
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center space-x-6 mb-8">
        <SkeletonLoader variant="circular" width={120} height={120} />
        <div className="flex-1 space-y-3">
          <SkeletonLoader variant="text" width={200} />
          <SkeletonLoader variant="text" width={150} />
          <SkeletonLoader variant="text" width={100} />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="space-y-3">
          <SkeletonLoader variant="text" width={100} />
          <SkeletonLoader variant="text" lines={3} />
        </div>
        <div className="space-y-3">
          <SkeletonLoader variant="text" width={120} />
          <SkeletonLoader variant="text" lines={3} />
        </div>
        <div className="space-y-3">
          <SkeletonLoader variant="text" width={80} />
          <SkeletonLoader variant="text" lines={3} />
        </div>
      </div>
    </div>
  </div>
);

export const AdminDashboardSkeleton: React.FC = () => (
  <div className="space-y-6">
    {/* Stats Cards */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <SkeletonLoader variant="text" width={100} />
          <SkeletonLoader variant="text" width={150} className="mt-2" />
          <SkeletonLoader variant="text" width={80} className="mt-2" />
        </div>
      ))}
    </div>
    
    {/* Charts and Tables */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <SkeletonLoader variant="text" width={120} />
        <SkeletonLoader variant="rectangular" height={300} className="mt-4" />
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <SkeletonLoader variant="text" width={100} />
        <div className="mt-4 space-y-3">
          {Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="flex items-center justify-between">
              <SkeletonLoader variant="text" width={150} />
              <SkeletonLoader variant="text" width={80} />
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);

export default LoadingState;
