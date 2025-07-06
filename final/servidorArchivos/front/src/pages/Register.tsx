import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { useAuth } from '../contexts/AuthContext';

const Register: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const { register, error } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Form validation
    if (!username || !password || !confirmPassword) {
      setFormError('Todos los campos son obligatorios');
      return;
    }
    
    if (password !== confirmPassword) {
      setFormError('Las contraseñas no coinciden');
      return;
    }
    
    setFormError(null);
    setIsLoading(true);
    
    try {
      const success = await register(username, password);
      if (success) {
        // Redirect to login page after successful registration
        navigate('/login', { state: { message: 'Registro exitoso. Ahora puedes iniciar sesión.' } });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <RegisterContainer>
      <RegisterCard>
        <h1>Crear Cuenta</h1>
        <p>Regístrate para acceder al servidor de archivos</p>
        
        {(formError || error) && <ErrorMessage>{formError || error}</ErrorMessage>}
        
        <RegisterForm onSubmit={handleSubmit}>
          <FormGroup>
            <Label htmlFor="username">Usuario</Label>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Elige un nombre de usuario"
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
              placeholder="Crea una contraseña"
              required
            />
          </FormGroup>
          
          <FormGroup>
            <Label htmlFor="confirmPassword">Confirmar Contraseña</Label>
            <Input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Repite tu contraseña"
              required
            />
          </FormGroup>
          
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Registrando...' : 'Registrarse'}
          </Button>
        </RegisterForm>
        
        <LoginLink>
          ¿Ya tienes una cuenta? <Link to="/login">Inicia sesión</Link>
        </LoginLink>
      </RegisterCard>
    </RegisterContainer>
  );
};

// Styled components
const RegisterContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  background-color: #f5f5f5;
`;

const RegisterCard = styled.div`
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

const RegisterForm = styled.form`
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

const LoginLink = styled.div`
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

export default Register;