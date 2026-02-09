import { useState } from 'react';
import { SignUpForm } from '../components/Auth/SignUpForm';
import { LoginForm } from '../components/Auth/LoginForm';
import { Button } from '../components/ui/button';

export function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);

  if (isLogin) {
    return <LoginForm onToggleMode={() => setIsLogin(false)} />;
  }

  return <SignUpForm onToggleMode={() => setIsLogin(true)} />;
}