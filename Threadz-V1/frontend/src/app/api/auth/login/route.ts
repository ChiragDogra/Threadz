import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json();

    // Mock authentication logic
    if (email === 'Threadz2026@gmail.com' && password === 'Threadz87651234') {
      return NextResponse.json({
        user: {
          user_id: 'admin-001',
          email: 'Threadz2026@gmail.com',
          full_name: 'Threadz Admin',
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
