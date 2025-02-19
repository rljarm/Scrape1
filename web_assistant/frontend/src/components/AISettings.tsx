import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  FormControl,
  FormControlLabel,
  Switch,
  TextField,
  Select,
  MenuItem,
  InputLabel,
  Grid,
  Button,
  Divider,
} from '@mui/material';

interface AIConfig {
  enabled: boolean;
  model: string;
  temperature: number;
  maxTokens: number;
  searchAPI: string;
  youtubeEnabled: boolean;
  extractTranscripts: boolean;
  contentClassification: boolean;
  summarization: boolean;
  apiKeys: {
    openai: string;
    bing: string;
    google: string;
    brave: string;
  };
}

const initialConfig: AIConfig = {
  enabled: false,
  model: 'gpt-4',
  temperature: 0.7,
  maxTokens: 2000,
  searchAPI: 'bing',
  youtubeEnabled: false,
  extractTranscripts: false,
  contentClassification: true,
  summarization: true,
  apiKeys: {
    openai: '',
    bing: '',
    google: '',
    brave: '',
  },
};

const AISettings: React.FC = () => {
  const [config, setConfig] = useState<AIConfig>(initialConfig);

  const handleChange = (
    event: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>
  ) => {
    const { name, value, checked } = event.target as any;
    
    if (name?.includes('.')) {
      const [parent, child] = name.split('.');
      setConfig(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent as keyof AIConfig],
          [child]: value,
        },
      }));
    } else {
      setConfig(prev => ({
        ...prev,
        [name as keyof AIConfig]: event.target.type === 'checkbox' ? checked : value,
      }));
    }
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    // TODO: Submit AI settings to backend
    console.log('Submitting AI settings:', config);
  };

  return (
    <Box sx={{ flexGrow: 1, mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        AI Settings
      </Typography>

      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.enabled}
                    onChange={handleChange}
                    name="enabled"
                  />
                }
                label="Enable AI Processing"
              />
            </Grid>

            <Grid item xs={12}>
              <Divider />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth disabled={!config.enabled}>
                <InputLabel>Model</InputLabel>
                <Select
                  name="model"
                  value={config.model}
                  onChange={handleChange}
                  label="Model"
                >
                  <MenuItem value="gpt-4">GPT-4</MenuItem>
                  <MenuItem value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>
                  <MenuItem value="claude-2">Claude 2</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Temperature"
                name="temperature"
                value={config.temperature}
                onChange={handleChange}
                disabled={!config.enabled}
                inputProps={{ min: 0, max: 1, step: 0.1 }}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Max Tokens"
                name="maxTokens"
                value={config.maxTokens}
                onChange={handleChange}
                disabled={!config.enabled}
                inputProps={{ min: 100, max: 4000 }}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth disabled={!config.enabled}>
                <InputLabel>Search API</InputLabel>
                <Select
                  name="searchAPI"
                  value={config.searchAPI}
                  onChange={handleChange}
                  label="Search API"
                >
                  <MenuItem value="bing">Bing</MenuItem>
                  <MenuItem value="google">Google</MenuItem>
                  <MenuItem value="brave">Brave</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <Divider />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.youtubeEnabled}
                    onChange={handleChange}
                    name="youtubeEnabled"
                    disabled={!config.enabled}
                  />
                }
                label="Enable YouTube Processing"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.extractTranscripts}
                    onChange={handleChange}
                    name="extractTranscripts"
                    disabled={!config.enabled || !config.youtubeEnabled}
                  />
                }
                label="Extract Video Transcripts"
              />
            </Grid>

            <Grid item xs={12}>
              <Divider />
            </Grid>

            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                API Keys
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="password"
                label="OpenAI API Key"
                name="apiKeys.openai"
                value={config.apiKeys.openai}
                onChange={handleChange}
                disabled={!config.enabled}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="password"
                label="Bing API Key"
                name="apiKeys.bing"
                value={config.apiKeys.bing}
                onChange={handleChange}
                disabled={!config.enabled || config.searchAPI !== 'bing'}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="password"
                label="Google API Key"
                name="apiKeys.google"
                value={config.apiKeys.google}
                onChange={handleChange}
                disabled={!config.enabled || config.searchAPI !== 'google'}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="password"
                label="Brave API Key"
                name="apiKeys.brave"
                value={config.apiKeys.brave}
                onChange={handleChange}
                disabled={!config.enabled || config.searchAPI !== 'brave'}
              />
            </Grid>

            <Grid item xs={12}>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                size="large"
                fullWidth
                disabled={!config.enabled}
              >
                Save AI Settings
              </Button>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  );
};

export default AISettings;
