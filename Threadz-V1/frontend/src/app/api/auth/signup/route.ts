import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { email, password, full_name } = await request.json();

    // Mock user creation logic
    const newUser = {
      user_id: 'user-' + Date.now(),
      email,
      full_name,
      role: 'user'
    };

    return NextResponse.json({
      user: newUser,
      access_token: 'mock-token-' + Date.now()
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Registration failed' },
      { status: 500 }
    );
  }
}
