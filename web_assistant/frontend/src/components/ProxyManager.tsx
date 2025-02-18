import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

interface Proxy {
  id: string;
  host: string;
  port: number;
  username?: string;
  password?: string;
  status: 'active' | 'failed' | 'banned';
  lastUsed: string;
  successRate: number;
}

const ProxyManager: React.FC = () => {
  const [newProxy, setNewProxy] = useState({
    host: '',
    port: '',
    username: '',
    password: '',
  });

  const [proxies, setProxies] = useState<Proxy[]>([
    {
      id: '1',
      host: '192.168.1.1',
      port: 8080,
      username: 'user1',
      status: 'active',
      lastUsed: '2025-02-16T14:30:00',
      successRate: 98.5,
    },
    {
      id: '2',
      host: '192.168.1.2',
      port: 8081,
      status: 'failed',
      lastUsed: '2025-02-16T14:25:00',
      successRate: 45.2,
    },
  ]);

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setNewProxy(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleAddProxy = (event: React.FormEvent) => {
    event.preventDefault();
    // TODO: Validate and add proxy to backend
    console.log('Adding proxy:', newProxy);
  };

  const handleDeleteProxy = (id: string) => {
    // TODO: Delete proxy from backend
    setProxies(prev => prev.filter(proxy => proxy.id !== id));
  };

  const getStatusChip = (status: Proxy['status']) => {
    const statusConfig = {
      active: { color: 'success', icon: <CheckCircleIcon /> },
      failed: { color: 'error', icon: <ErrorIcon /> },
      banned: { color: 'warning', icon: <ErrorIcon /> },
    };

    const config = statusConfig[status];
    return (
      <Chip
        label={status.toUpperCase()}
        color={config.color as any}
        icon={config.icon}
        size="small"
      />
    );
  };

  return (
    <Box sx={{ flexGrow: 1, mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Proxy Manager
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <form onSubmit={handleAddProxy}>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <TextField
              required
              label="Host"
              name="host"
              value={newProxy.host}
              onChange={handleInputChange}
            />
            <TextField
              required
              label="Port"
              name="port"
              type="number"
              value={newProxy.port}
              onChange={handleInputChange}
            />
            <TextField
              label="Username"
              name="username"
              value={newProxy.username}
              onChange={handleInputChange}
            />
            <TextField
              label="Password"
              name="password"
              type="password"
              value={newProxy.password}
              onChange={handleInputChange}
            />
            <Button type="submit" variant="contained" color="primary">
              Add Proxy
            </Button>
          </Box>
        </form>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Host</TableCell>
              <TableCell>Port</TableCell>
              <TableCell>Username</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Last Used</TableCell>
              <TableCell>Success Rate</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {proxies.map((proxy) => (
              <TableRow key={proxy.id}>
                <TableCell>{proxy.host}</TableCell>
                <TableCell>{proxy.port}</TableCell>
                <TableCell>{proxy.username || '-'}</TableCell>
                <TableCell>{getStatusChip(proxy.status)}</TableCell>
                <TableCell>
                  {new Date(proxy.lastUsed).toLocaleString()}
                </TableCell>
                <TableCell>{`${proxy.successRate}%`}</TableCell>
                <TableCell>
                  <IconButton
                    onClick={() => handleDeleteProxy(proxy.id)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default ProxyManager;
