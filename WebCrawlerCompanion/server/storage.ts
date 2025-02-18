import { ProxyConfig, InsertProxyConfig, Selector, InsertSelector } from "@shared/schema";

export interface IStorage {
  getProxyConfigs(): Promise<ProxyConfig[]>;
  createProxyConfig(config: InsertProxyConfig): Promise<ProxyConfig>;
  getSelectors(): Promise<Selector[]>;
  createSelector(selector: InsertSelector): Promise<Selector>;
}

export class MemStorage implements IStorage {
  private proxyConfigs: Map<number, ProxyConfig>;
  private selectors: Map<number, Selector>;
  private currentProxyId: number;
  private currentSelectorId: number;

  constructor() {
    this.proxyConfigs = new Map();
    this.selectors = new Map();
    this.currentProxyId = 1;
    this.currentSelectorId = 1;
  }

  async getProxyConfigs(): Promise<ProxyConfig[]> {
    return Array.from(this.proxyConfigs.values());
  }

  async createProxyConfig(config: InsertProxyConfig): Promise<ProxyConfig> {
    const id = this.currentProxyId++;
    const proxyConfig: ProxyConfig = { ...config, id };
    this.proxyConfigs.set(id, proxyConfig);
    return proxyConfig;
  }

  async getSelectors(): Promise<Selector[]> {
    return Array.from(this.selectors.values());
  }

  async createSelector(selector: InsertSelector): Promise<Selector> {
    const id = this.currentSelectorId++;
    const newSelector: Selector = { ...selector, id };
    this.selectors.set(id, newSelector);
    return newSelector;
  }
}

export const storage = new MemStorage();
