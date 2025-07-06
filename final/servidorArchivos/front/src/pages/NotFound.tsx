import React from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { useAuth } from '../contexts/AuthContext';

const NotFound: React.FC = () => {
  const { isAuthenticated } = useAuth();
  
  return (
    <NotFoundContainer>
      <NotFoundContent>
        <h1>404</h1>
        <h2>Página no encontrada</h2>
        <p>Lo sentimos, la página que estás buscando no existe.</p>
        
        <BackLink to={isAuthenticated ? '/' : '/login'}>
          Volver a {isAuthenticated ? 'Mis Archivos' : 'Iniciar Sesión'}
        </BackLink>
      </NotFoundContent>
    </NotFoundContainer>
  );
};

// Styled components
const NotFoundContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 20px;
`;

const NotFoundContent = styled.div`
  text-align: center;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 40px;
  max-width: 400px;
  width: 100%;
  
  h1 {
    font-size: 72px;
    margin: 0;
    color: #0066ff;
  }
  
  h2 {
    margin: 10px 0;
    color: #333;
  }
  
  p {
    margin-bottom: 30px;
    color: #666;
  }
`;

const BackLink = styled(Link)`
  display: inline-block;
  background-color: #0066ff;
  color: white;
  text-decoration: none;
  padding: 10px 20px;
  border-radius: 4px;
  font-weight: 500;
  
  &:hover {
    background-color: #0052cc;
  }
`;

export default NotFound;