import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { useAuth } from '../contexts/AuthContext';
// Import the logo
import logoFacultad from '../assets/logo.jpg';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, error } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!username || !password) {
      return;
    }

    setIsLoading(true);

    try {
      const success = await login(username, password);
      if (success) {
        navigate('/');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <LoginContainer>
      <LoginCard>
        <LogoContainer>
          <Logo src={logoFacultad} alt="Logo de la Facultad" />
        </LogoContainer>
        <AppTitle>Servidor de Archivos</AppTitle>
        <AppSubtitle>Computación II - Juan Manuel Aidar</AppSubtitle>

        <h1>Iniciar Sesión</h1>
        <p>Accede a tu cuenta para gestionar tus archivos</p>

        {error && <ErrorMessage>{error}</ErrorMessage>}

        <LoginForm onSubmit={handleSubmit}>
          <FormGroup>
            <Label htmlFor="username">Usuario</Label>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Ingresa tu nombre de usuario"
              required
            />
          </FormGroup>

          <FormGroup>
            <Label htmlFor="password">Contraseña</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Ingresa tu contraseña"
              required
            />
          </FormGroup>

          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
          </Button>
        </LoginForm>

        <RegisterLink>
          ¿No tienes una cuenta? <Link to="/register">Regístrate</Link>
        </RegisterLink>
      </LoginCard>
    </LoginContainer>
  );
};

// Styled components
const LoginContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  background-color: #f5f5f5;
`;

const LoginCard = styled.div`
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 30px;
  width: 100%;
  max-width: 400px;

  h1 {
    margin: 0 0 10px;
    color: #333;
    font-size: 24px;
  }

  p {
    margin: 0 0 20px;
    color: #666;
  }
`;

const LoginForm = styled.form`
  display: flex;
  flex-direction: column;
  gap: 15px;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 5px;
`;

const Label = styled.label`
  font-weight: 500;
  color: #333;
`;

const Input = styled.input`
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;

  &:focus {
    outline: none;
    border-color: #0066ff;
  }
`;

const Button = styled.button`
  background-color: #0066ff;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 12px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  margin-top: 10px;

  &:hover {
    background-color: #0052cc;
  }

  &:disabled {
    background-color: #99c2ff;
    cursor: not-allowed;
  }
`;

const ErrorMessage = styled.div`
  background-color: #ffebee;
  color: #c62828;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 15px;
`;

const RegisterLink = styled.div`
  margin-top: 20px;
  text-align: center;
  color: #666;

  a {
    color: #0066ff;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
`;

const AppTitle = styled.h2`
  color: #0066ff;
  font-size: 28px;
  text-align: center;
  margin: 0 0 5px;
`;

const AppSubtitle = styled.h3`
  color: #666;
  font-size: 16px;
  font-weight: normal;
  text-align: center;
  margin: 0 0 25px;
`;

const LogoContainer = styled.div`
  display: flex;
  justify-content: center;
  margin-bottom: 15px;
`;

const Logo = styled.img`
  max-width: 150px;
  height: auto;
  border-radius: 8px;
`;

export default Login;
