// src/app/components/AuthGuard.tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getCurrentUser } from '@/lib/auth';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        console.log('🔍 Checking user authentication...');
        const user = await getCurrentUser();
        if (!user) {
          console.log('⚠️ No user found, redirecting to login');
          setIsAuthenticated(false);
          setIsLoading(false);
          router.push('/login');
        } else {
          console.log('✅ User authenticated:', user);
          setIsAuthenticated(true);
          setIsLoading(false);
        }
      } catch (error) {
        console.error('❌ Auth check failed:', error);
        setIsAuthenticated(false);
        setIsLoading(false);
        // Only redirect after a short delay to ensure user sees loading state first
        setTimeout(() => {
          router.push('/login');
        }, 500);
      }
    };

    checkAuth();
  }, [router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect to login
  }

  return <>{children}</>;
}