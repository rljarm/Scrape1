// CRITICAL: Base URL for API endpoints
// TODO(future): Add environment-based configuration
// CHECK(periodic): Verify API endpoint health

const API_BASE_URL = 'http://95.211.93.240:6666/api';

// API endpoints
const CRAWL_API = `${API_BASE_URL}/crawling`;
const SELECTOR_API = `${CRAWL_API}/selectors`;
const CONFIG_API = `${CRAWL_API}/configs`;
const AUTH_API = `${API_BASE_URL}/token`;

// API request helper with error handling
const handleRequest = async (url: string, options: RequestInit = {}) => {
  try {
    const token = localStorage.getItem('accessToken');
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

// Authentication
export const login = (username: string, password: string) =>
  handleRequest(`${AUTH_API}/`, {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });

export const refreshToken = (refreshToken: string) =>
  handleRequest(`${AUTH_API}/refresh/`, {
    method: 'POST',
    body: JSON.stringify({ refresh: refreshToken }),
  });

// Selector management
export const createSelector = (selectorData: any) =>
  handleRequest(`${SELECTOR_API}/`, {
    method: 'POST',
    body: JSON.stringify(selectorData),
  });

export const getSelector = (id: string) =>
  handleRequest(`${SELECTOR_API}/${id}/`);

export const updateSelector = (id: string, selectorData: any) =>
  handleRequest(`${SELECTOR_API}/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(selectorData),
  });

export const deleteSelector = (id: string) =>
  handleRequest(`${SELECTOR_API}/${id}/`, {
    method: 'DELETE',
  });

// Configuration management
export const createConfig = (configData: any) =>
  handleRequest(`${CONFIG_API}/`, {
    method: 'POST',
    body: JSON.stringify(configData),
  });

export const getConfig = (id: string) =>
  handleRequest(`${CONFIG_API}/${id}/`);

export const updateConfig = (id: string, configData: any) =>
  handleRequest(`${CONFIG_API}/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(configData),
  });

export const deleteConfig = (id: string) =>
  handleRequest(`${CONFIG_API}/${id}/`, {
    method: 'DELETE',
  });

export const getAllConfigs = () =>
  handleRequest(`${CONFIG_API}/`);

export const testSelectors = (configId: string) =>
  handleRequest(`${CONFIG_API}/${configId}/test_selectors/`, {
    method: 'POST',
  });

// Page analysis
export const analyzePage = (url: string) =>
  handleRequest(`${CRAWL_API}/analyze/`, {
    method: 'POST',
    body: JSON.stringify({ url }),
  });

// Crawl execution
export const executeCrawl = (configId: string) =>
  handleRequest(`${CRAWL_API}/execute/`, {
    method: 'POST',
    body: JSON.stringify({ configId }),
  });

export const getCrawlStatus = (crawlId: string) =>
  handleRequest(`${CRAWL_API}/status/${crawlId}/`);

export const stopCrawl = (crawlId: string) =>
  handleRequest(`${CRAWL_API}/stop/${crawlId}/`, {
    method: 'POST',
  });

// Export results
export const exportResults = (crawlId: string, format: string) =>
  handleRequest(`${CRAWL_API}/export/${crawlId}/`, {
    method: 'POST',
    body: JSON.stringify({ format }),
  });
