import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';

// CRITICAL: This component shows crawl configurations overview
// TODO(future): Add configuration search and filtering
// CHECK(periodic): Verify data loading performance

const Container = styled.div`
  padding: 1rem;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
`;

const CreateButton = styled.button`
  padding: 0.5rem 1rem;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;

  &:hover {
    background-color: #218838;
  }
`;

const ConfigList = styled.div`
  display: grid;
  gap: 1rem;
`;

const ConfigCard = styled.div`
  padding: 1rem;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: grid;
  gap: 0.5rem;
`;

const ConfigName = styled.h3`
  margin: 0;
  color: #343a40;
`;

const ConfigUrl = styled.div`
  color: #6c757d;
  font-size: 0.9rem;
`;

const ConfigStats = styled.div`
  display: flex;
  gap: 1rem;
  color: #6c757d;
  font-size: 0.9rem;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
`;

const ActionButton = styled.button<{ variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: 0.25rem 0.75rem;
  background-color: ${props => 
    props.variant === 'danger' ? '#dc3545' :
    props.variant === 'secondary' ? '#6c757d' :
    '#007bff'};
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;

  &:hover {
    background-color: ${props => 
      props.variant === 'danger' ? '#c82333' :
      props.variant === 'secondary' ? '#5a6268' :
      '#0056b3'};
  }
`;

// Mock data - replace with API calls
const mockConfigs = [
  {
    id: 1,
    name: 'Example Configuration',
    url: 'https://example.com',
    selectors: 3,
    lastRun: '2025-02-16',
    status: 'completed'
  },
  {
    id: 2,
    name: 'Test Configuration',
    url: 'https://test.com',
    selectors: 5,
    lastRun: '2025-02-15',
    status: 'failed'
  }
];

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [configs, setConfigs] = useState(mockConfigs);
  const [loading, setLoading] = useState(false);

  // TODO: Replace with actual API call
  useEffect(() => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setConfigs(mockConfigs);
      setLoading(false);
    }, 500);
  }, []);

  const handleCreate = () => {
    navigate('/config');
  };

  const handleEdit = (id: number) => {
    navigate(`/config/${id}`);
  };

  const handleRun = (id: number) => {
    console.log('Running configuration:', id);
    // TODO: Implement run functionality
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this configuration?')) {
      setConfigs(configs.filter(config => config.id !== id));
      // TODO: Implement actual delete API call
    }
  };

  return (
    <Container>
      <Header>
        <h2>Crawl Configurations</h2>
        <CreateButton onClick={handleCreate}>
          Create New Configuration
        </CreateButton>
      </Header>

      {loading ? (
        <div>Loading configurations...</div>
      ) : (
        <ConfigList>
          {configs.map(config => (
            <ConfigCard key={config.id}>
              <ConfigName>{config.name}</ConfigName>
              <ConfigUrl>{config.url}</ConfigUrl>
              <ConfigStats>
                <span>{config.selectors} selectors</span>
                <span>Last run: {config.lastRun}</span>
                <span>Status: {config.status}</span>
              </ConfigStats>
              <ButtonGroup>
                <ActionButton onClick={() => handleEdit(config.id)}>
                  Edit
                </ActionButton>
                <ActionButton onClick={() => handleRun(config.id)} variant="secondary">
                  Run
                </ActionButton>
                <ActionButton onClick={() => handleDelete(config.id)} variant="danger">
                  Delete
                </ActionButton>
              </ButtonGroup>
            </ConfigCard>
          ))}
        </ConfigList>
      )}
    </Container>
  );
};

export default Dashboard;
