// CRITICAL: Environment configuration management
// TODO(future): Add configuration validation
// CHECK(periodic): Verify environment variables

interface Config {
  api: {
    baseUrl: string;
    wsUrl: string;
  };
  features: {
    mockApi: boolean;
    debugLogging: boolean;
  };
  ui: {
    maxIframeHeight: number;
    defaultPageSize: number;
  };
  auth: {
    tokenKey: string;
    refreshInterval: number;
  };
  performance: {
    wsReconnectAttempts: number;
    wsReconnectInterval: number;
  };
}

const getEnvVar = (key: string, defaultValue?: string): string => {
  const value = process.env[`REACT_APP_${key}`];
  if (!value && defaultValue === undefined) {
    throw new Error(`Environment variable REACT_APP_${key} is not defined`);
  }
  return value || defaultValue || '';
};

const getEnvVarNumber = (key: string, defaultValue?: number): number => {
  const value = getEnvVar(key, defaultValue?.toString());
  const numValue = Number(value);
  if (isNaN(numValue)) {
    throw new Error(`Environment variable REACT_APP_${key} is not a valid number`);
  }
  return numValue;
};

const getEnvVarBool = (key: string, defaultValue?: boolean): boolean => {
  const value = getEnvVar(key, defaultValue?.toString());
  return value.toLowerCase() === 'true';
};

export const config: Config = {
  api: {
    baseUrl: getEnvVar('API_URL', 'http://95.211.93.240:6666/api'),
    wsUrl: getEnvVar('WS_URL', 'ws://95.211.93.240:6666'),
  },
  features: {
    mockApi: getEnvVarBool('ENABLE_MOCK_API', false),
    debugLogging: getEnvVarBool('ENABLE_DEBUG_LOGGING', true),
  },
  ui: {
    maxIframeHeight: getEnvVarNumber('MAX_IFRAME_HEIGHT', 600),
    defaultPageSize: getEnvVarNumber('DEFAULT_PAGE_SIZE', 10),
  },
  auth: {
    tokenKey: getEnvVar('JWT_STORAGE_KEY', 'web_assistant_token'),
    refreshInterval: getEnvVarNumber('TOKEN_REFRESH_INTERVAL', 55),
  },
  performance: {
    wsReconnectAttempts: getEnvVarNumber('WEBSOCKET_RECONNECT_ATTEMPTS', 5),
    wsReconnectInterval: getEnvVarNumber('WEBSOCKET_RECONNECT_INTERVAL', 2000),
  },
};

// Logging utility for debugging
export const log = {
  debug: (...args: any[]) => {
    if (config.features.debugLogging) {
      console.debug('[Web Assistant]', ...args);
    }
  },
  error: (...args: any[]) => {
    console.error('[Web Assistant]', ...args);
  },
  warn: (...args: any[]) => {
    console.warn('[Web Assistant]', ...args);
  },
  info: (...args: any[]) => {
    console.info('[Web Assistant]', ...args);
  },
};

export default config;
