import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json();

    // Mock authentication logic
    if (email === 'admin@example.com' && password === 'admin123') {
      return NextResponse.json({
        user: {
          user_id: 'admin-001',
          email: 'admin@example.com',
          full_name: 'Admin User',
          role: 'admin'
        },
        access_token: 'mock-admin-token-' + Date.now()
      });
    }

    if (email === 'user@example.com' && password === 'user123') {
      return NextResponse.json({
        user: {
          user_id: 'user-001',
          email: 'user@example.com',
          full_name: 'Test User',
          role: 'user'
        },
        access_token: 'mock-user-token-' + Date.now()
      });
    }

    return NextResponse.json(
      { error: 'Invalid credentials' },
      { status: 401 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: 'Login failed' },
      { status: 500 }
    );
  }
}
