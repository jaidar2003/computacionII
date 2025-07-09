import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { FiUpload, FiDownload, FiTrash2, FiLogOut, FiFile, FiFolder, FiEdit, FiCheckCircle } from 'react-icons/fi';

interface FileItem {
  name: string;
  size: number;
  modified: string;
  type: 'file' | 'directory';
}

const Dashboard: React.FC = () => {
  const { user, userRole, logout } = useAuth();
  const [files, setFiles] = useState<FileItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isRenameModalOpen, setIsRenameModalOpen] = useState(false);
  const [newFileName, setNewFileName] = useState('');
  const [verificationStatus, setVerificationStatus] = useState<{status: string, message: string} | null>(null);

  // Fetch files on component mount and periodically refresh
  useEffect(() => {
    fetchFiles();

    // Set up interval to refresh files every 10 seconds
    const interval = setInterval(() => {
      fetchFiles();
    }, 10000);

    // Clean up interval on component unmount
    return () => clearInterval(interval);
  }, []);

  const fetchFiles = async (retryCount = 0) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.get('/api/files', { withCredentials: true });
      console.log('API response:', response.data); // Debug log
      setFiles(response.data.files || []);
    } catch (err: any) {
      console.error('Error fetching files:', err);

      // Retry up to 3 times with exponential backoff
      if (retryCount < 3) {
        console.log(`Retrying fetch (attempt ${retryCount + 1})...`);
        setTimeout(() => {
          fetchFiles(retryCount + 1);
        }, 1000 * Math.pow(2, retryCount)); // 1s, 2s, 4s backoff
        return;
      }

      setError(err.response?.data?.error || 'Error al cargar archivos');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = (file: FileItem) => {
    setSelectedFile(file === selectedFile ? null : file);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    const formData = new FormData();
    formData.append('file', file);

    setUploadProgress(0);
    setError(null);

    try {
      await axios.post('/api/files/upload', formData, {
        withCredentials: true,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(progress);
          }
        },
      });

      // Refresh file list after upload
      fetchFiles();
      setUploadProgress(null);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al subir archivo');
      setUploadProgress(null);
      console.error('Error uploading file:', err);
    }
  };

  const handleFileDownload = async (fileName: string) => {
    try {
      window.open(`/api/files/download/${fileName}`, '_blank');
    } catch (err) {
      console.error('Error downloading file:', err);
    }
  };

  const handleFileDelete = async (fileName: string) => {
    if (!confirm(`¿Estás seguro de que deseas eliminar ${fileName}?`)) {
      return;
    }

    try {
      await axios.delete(`/api/files/${fileName}`, { withCredentials: true });
      fetchFiles();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al eliminar archivo');
      console.error('Error deleting file:', err);
    }
  };

  const handleFileRename = async () => {
    if (!selectedFile || !newFileName) return;

    try {
      const response = await axios.put('/api/files/rename', {
        oldName: selectedFile.name,
        newName: newFileName
      }, { withCredentials: true });

      if (response.data.success) {
        setIsRenameModalOpen(false);
        setNewFileName('');
        fetchFiles();
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al renombrar archivo');
      console.error('Error renaming file:', err);
    }
  };

  const handleFileVerify = async (fileName: string) => {
    try {
      const response = await axios.get(`/api/files/verify/${fileName}`, { withCredentials: true });

      if (response.data.success) {
        setVerificationStatus({
          status: response.data.status,
          message: response.data.message
        });
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al verificar archivo');
      console.error('Error verifying file:', err);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <DashboardContainer>
      <Header>
        <h1>Servidor de Archivos</h1>
        <UserInfo>
          <span>Hola, {user}</span>
          <RoleBadge>{userRole === 'admin' ? 'Administrador' : 'Usuario'}</RoleBadge>
          <LogoutButton onClick={logout}>
            <FiLogOut /> Salir
          </LogoutButton>
        </UserInfo>
      </Header>

      <Content>
        <Sidebar>
          <SidebarTitle>Acciones</SidebarTitle>
          <UploadButton>
            <FiUpload /> Subir Archivo
            <input 
              type="file" 
              onChange={handleFileUpload} 
              style={{ opacity: 0, position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', cursor: 'pointer' }} 
            />
          </UploadButton>

          {uploadProgress !== null && (
            <ProgressContainer>
              <ProgressBar progress={uploadProgress} />
              <span>{uploadProgress}%</span>
            </ProgressContainer>
          )}

          {selectedFile && (
            <ActionButtons>
              <ActionButton onClick={() => handleFileDownload(selectedFile.name)}>
                <FiDownload /> Descargar
              </ActionButton>
              <ActionButton onClick={() => setIsRenameModalOpen(true)}>
                <FiEdit /> Renombrar
              </ActionButton>
              <ActionButton onClick={() => handleFileVerify(selectedFile.name)}>
                <FiCheckCircle /> Verificar
              </ActionButton>
              <ActionButton onClick={() => handleFileDelete(selectedFile.name)}>
                <FiTrash2 /> Eliminar
              </ActionButton>
            </ActionButtons>
          )}
        </Sidebar>

        <MainContent>
          <ContentHeader>
            <h2>Mis Archivos</h2>
            <RefreshButton onClick={fetchFiles}>Actualizar</RefreshButton>
          </ContentHeader>

          {error && <ErrorMessage>{error}</ErrorMessage>}

          {isLoading ? (
            <LoadingMessage>Cargando archivos...</LoadingMessage>
          ) : files.length === 0 ? (
            <EmptyState>
              <p>No tienes archivos almacenados.</p>
              <p>Sube tu primer archivo haciendo clic en "Subir Archivo".</p>
            </EmptyState>
          ) : (
            <FileList>
              <FileListHeader>
                <div>Nombre</div>
                <div>Tamaño</div>
                <div>Modificado</div>
              </FileListHeader>

              {files.map((file) => (
                <FileItem 
                  key={file.name} 
                  onClick={() => handleFileSelect(file)}
                  selected={selectedFile?.name === file.name}
                >
                  <FileName>
                    {file.type === 'directory' ? <FiFolder /> : <FiFile />}
                    {file.name}
                  </FileName>
                  <div>{formatFileSize(file.size)}</div>
                  <div>{new Date(file.modified).toLocaleString()}</div>
                </FileItem>
              ))}
            </FileList>
          )}
        </MainContent>
      </Content>

      {isRenameModalOpen && selectedFile && (
        <Modal>
          <ModalContent>
            <h3>Renombrar Archivo</h3>
            <p>Nombre actual: {selectedFile.name}</p>
            <input
              type="text"
              value={newFileName}
              onChange={(e) => setNewFileName(e.target.value)}
              placeholder="Nuevo nombre"
            />
            <ModalButtons>
              <Button onClick={() => setIsRenameModalOpen(false)}>Cancelar</Button>
              <Button primary onClick={handleFileRename}>Renombrar</Button>
            </ModalButtons>
          </ModalContent>
        </Modal>
      )}

      {verificationStatus && (
        <VerificationStatus status={verificationStatus.status}>
          <h3>Resultado de la Verificación</h3>
          <p>{verificationStatus.message}</p>
          <Button onClick={() => setVerificationStatus(null)}>Cerrar</Button>
        </VerificationStatus>
      )}
    </DashboardContainer>
  );
};

// Styled components
const DashboardContainer = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f5f5f5;
`;

const Header = styled.header`
  background-color: #0066ff;
  color: white;
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  h1 {
    margin: 0;
    font-size: 20px;
  }
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 15px;
`;

const RoleBadge = styled.div`
  background-color: ${props => props.children === 'Administrador' ? '#ff9800' : '#4caf50'};
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-left: 10px;
  font-weight: bold;
`;

const LogoutButton = styled.button`
  background: none;
  border: none;
  color: white;
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 4px;

  &:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }
`;

const Content = styled.div`
  display: flex;
  flex: 1;
  padding: 20px;
  gap: 20px;

  @media (max-width: 768px) {
    flex-direction: column;
  }
`;

const Sidebar = styled.div`
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 20px;
  width: 250px;

  @media (max-width: 768px) {
    width: auto;
  }
`;

const SidebarTitle = styled.h2`
  font-size: 16px;
  margin: 0 0 15px;
  color: #333;
`;

const UploadButton = styled.div`
  background-color: #0066ff;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  position: relative;
  overflow: hidden;

  &:hover {
    background-color: #0052cc;
  }
`;

const ProgressContainer = styled.div`
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;

  span {
    font-size: 12px;
    text-align: center;
  }
`;

const ProgressBar = styled.div<{ progress: number }>`
  height: 6px;
  background-color: #e0e0e0;
  border-radius: 3px;
  overflow: hidden;
  position: relative;

  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: ${props => props.progress}%;
    background-color: #0066ff;
    transition: width 0.3s ease;
  }
`;

const ActionButtons = styled.div`
  margin-top: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const ActionButton = styled.button`
  background-color: #f5f5f5;
  color: #333;
  border: none;
  border-radius: 4px;
  padding: 8px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;

  &:hover {
    background-color: #e0e0e0;
  }
`;

const MainContent = styled.div`
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 20px;
  display: flex;
  flex-direction: column;
`;

const ContentHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  h2 {
    margin: 0;
    font-size: 18px;
    color: #333;
  }
`;

const RefreshButton = styled.button`
  background-color: #f5f5f5;
  color: #333;
  border: none;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 14px;
  cursor: pointer;

  &:hover {
    background-color: #e0e0e0;
  }
`;

const ErrorMessage = styled.div`
  background-color: #ffebee;
  color: #c62828;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 15px;
`;

const LoadingMessage = styled.div`
  text-align: center;
  padding: 40px;
  color: #666;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 40px;
  color: #666;

  p {
    margin: 5px 0;
  }
`;

const FileList = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
`;

const FileListHeader = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  padding: 10px 15px;
  background-color: #f5f5f5;
  border-radius: 4px 4px 0 0;
  font-weight: 500;
  color: #333;
`;

const FileItem = styled.div<{ selected: boolean }>`
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  padding: 10px 15px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  background-color: ${props => props.selected ? '#e3f2fd' : 'transparent'};

  &:hover {
    background-color: ${props => props.selected ? '#e3f2fd' : '#f9f9f9'};
  }
`;

const FileName = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;

  svg {
    color: #0066ff;
  }
`;

const Modal = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
`;

const ModalContent = styled.div`
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  width: 400px;
  max-width: 90%;

  h3 {
    margin-top: 0;
  }

  input {
    width: 100%;
    padding: 8px;
    margin: 10px 0;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
`;

const ModalButtons = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 15px;
`;

const Button = styled.button<{ primary?: boolean }>`
  background-color: ${props => props.primary ? '#0066ff' : '#f5f5f5'};
  color: ${props => props.primary ? 'white' : '#333'};
  border: none;
  border-radius: 4px;
  padding: 8px 12px;
  cursor: pointer;

  &:hover {
    background-color: ${props => props.primary ? '#0052cc' : '#e0e0e0'};
  }
`;

const VerificationStatus = styled.div<{ status: string }>`
  position: fixed;
  bottom: 20px;
  right: 20px;
  background-color: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  border-left: 5px solid ${props => {
    switch(props.status) {
      case 'ok': return '#4caf50';
      case 'corrupto': return '#f44336';
      case 'infectado': return '#ff9800';
      default: return '#2196f3';
    }
  }};
  max-width: 400px;
  z-index: 900;

  h3 {
    margin-top: 0;
    color: ${props => {
      switch(props.status) {
        case 'ok': return '#4caf50';
        case 'corrupto': return '#f44336';
        case 'infectado': return '#ff9800';
        default: return '#2196f3';
      }
    }};
  }
`;

export default Dashboard;
