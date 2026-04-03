const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8421";

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_URL;
  }

  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // Don't intercept auth endpoints — let the caller handle 401s
      const isAuthEndpoint = path.startsWith("/api/v1/auth/");
      if (isAuthEndpoint) {
        const text = await response.text();
        let detail = text;
        try {
          const json = JSON.parse(text);
          detail = json.detail || text;
        } catch {}
        throw new ApiError(401, detail);
      }

      // For non-auth endpoints, try refresh
      const refreshed = await this.refreshToken();
      if (refreshed) {
        headers["Authorization"] = `Bearer ${this.getToken()}`;
        const retry = await fetch(`${this.baseUrl}${path}`, {
          ...options,
          headers,
        });
        if (!retry.ok) throw new ApiError(retry.status, await retry.text());
        return retry.json();
      }
      // Refresh failed — clear tokens
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/auth/login";
      throw new ApiError(401, "Session expired");
    }

    if (!response.ok) {
      const text = await response.text();
      let detail = text;
      try {
        const json = JSON.parse(text);
        detail = json.detail || text;
      } catch {}
      throw new ApiError(response.status, detail);
    }

    return response.json();
  }

  private async refreshToken(): Promise<boolean> {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!response.ok) return false;
      const data = await response.json();
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  // Auth
  async setupStatus() {
    return this.request<{ has_admin: boolean; setup_complete: boolean }>(
      "/api/v1/auth/setup-status"
    );
  }

  async register(email: string, password: string, displayName?: string) {
    return this.request<{
      access_token: string;
      refresh_token: string;
      requires_2fa_setup: boolean;
    }>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, display_name: displayName }),
    });
  }

  async login(email: string, password: string, totpCode?: string) {
    return this.request<{
      access_token: string;
      refresh_token: string;
      requires_2fa_setup: boolean;
    }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password, totp_code: totpCode }),
    });
  }

  async totpSetup() {
    return this.request<{
      secret: string;
      provisioning_uri: string;
      qr_code_base64: string;
    }>("/api/v1/auth/totp/setup", { method: "POST" });
  }

  async totpVerify(code: string) {
    return this.request<{ success: boolean; message: string }>(
      "/api/v1/auth/totp/verify",
      { method: "POST", body: JSON.stringify({ code }) }
    );
  }

  // User
  async getMe() {
    return this.request<User>("/api/v1/users/me");
  }

  async updateMe(data: { display_name?: string }) {
    return this.request<User>("/api/v1/users/me", {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async changePassword(currentPassword: string, newPassword: string) {
    return this.request<{ message: string }>("/api/v1/auth/change-password", {
      method: "POST",
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
  }

  // Accounts
  async listAccounts() {
    return this.request<ConnectedAccount[]>("/api/v1/accounts/");
  }

  async startOAuth(provider: string) {
    return this.request<{ authorization_url: string; state: string }>(
      `/api/v1/accounts/${provider}/connect`
    );
  }

  async disconnectAccount(accountId: string) {
    return this.request(`/api/v1/accounts/${accountId}`, { method: "DELETE" });
  }

  // API Keys
  async listApiKeys() {
    return this.request<ApiKey[]>("/api/v1/api-keys/");
  }

  async createApiKey(data: {
    name: string;
    scopes?: Record<string, unknown>;
    allowed_providers?: string[];
  }) {
    return this.request<ApiKey & { key: string }>("/api/v1/api-keys/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async revokeApiKey(keyId: string) {
    return this.request(`/api/v1/api-keys/${keyId}`, { method: "DELETE" });
  }

  // Rules
  async listRules() {
    return this.request<Rule[]>("/api/v1/rules/");
  }

  async createRule(data: {
    name: string;
    description?: string;
    rule_type: string;
    conditions?: Record<string, unknown>;
    config?: Record<string, unknown>;
    priority?: number;
  }) {
    return this.request<Rule>("/api/v1/rules/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateRule(ruleId: string, data: Partial<Rule>) {
    return this.request<Rule>(`/api/v1/rules/${ruleId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteRule(ruleId: string) {
    return this.request(`/api/v1/rules/${ruleId}`, { method: "DELETE" });
  }

  // Providers
  async listProviders() {
    return this.request<{
      provider: string;
      display_name: string;
      is_configured: boolean;
      category: string;
      description: string;
      setup_url: string;
      docs_url: string | null;
    }[]>("/api/v1/providers/");
  }

  async configureProvider(provider: string, data: {
    provider: string;
    client_id: string;
    client_secret: string;
    extra_config?: Record<string, unknown>;
  }) {
    return this.request(`/api/v1/providers/${provider}/configure`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async removeProviderConfig(provider: string) {
    return this.request(`/api/v1/providers/${provider}/configure`, {
      method: "DELETE",
    });
  }

  // Security
  async getKillSwitchStatus() {
    return this.request<{
      is_active: boolean;
      activated_at: string | null;
      trigger_source: string | null;
      keys_revoked: number;
      tokens_revoked: number;
    }>("/api/v1/security/kill-switch/status");
  }

  async activateKillSwitch(data: {
    revoke_api_keys: boolean;
    disconnect_accounts?: boolean;
    reason?: string;
  }) {
    return this.request("/api/v1/security/kill-switch", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async listAnomalies(params?: { severity?: string; limit?: number }) {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined) query.set(k, String(v));
      });
    }
    return this.request<any[]>(`/api/v1/security/anomalies/?${query}`);
  }

  async acknowledgeAnomaly(anomalyId: string) {
    return this.request(`/api/v1/security/anomalies/${anomalyId}/acknowledge`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  }

  async scanSkill(data: {
    skill_name: string;
    skill_md_content?: string;
    files?: { path: string; content: string }[];
  }) {
    return this.request<any>("/api/v1/security/scan-skill", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Audit
  async listAuditLogs(params?: {
    action?: string;
    provider?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }) {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined) query.set(k, String(v));
      });
    }
    return this.request<AuditLog[]>(`/api/v1/audit/?${query}`);
  }

  async exportAuditLogs(params?: {
    start_date?: string;
    end_date?: string;
    action?: string;
    provider?: string;
    status?: string;
    limit?: number;
  }) {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined) query.set(k, String(v));
      });
    }
    const token = this.getToken();
    const res = await fetch(
      `${this.baseUrl}/api/v1/audit/export?${query}`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} }
    );
    return res.blob();
  }

  // Webhooks
  async listWebhooks() {
    return this.request<any[]>("/api/v1/webhooks/");
  }

  async createWebhook(data: {
    event_type: string;
    callback_url: string;
    connected_account_id?: string;
    filter_config?: Record<string, unknown>;
  }) {
    return this.request<any>("/api/v1/webhooks/subscribe", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async deleteWebhook(id: string) {
    return this.request(`/api/v1/webhooks/${id}`, { method: "DELETE" });
  }

  async listWebhookEvents(id: string) {
    return this.request<any[]>(`/api/v1/webhooks/${id}/events`);
  }

  // Notifications
  async getNotificationSettings() {
    return this.request<any>("/api/v1/notifications/settings");
  }

  async updateNotificationSettings(data: Record<string, unknown>) {
    return this.request<any>("/api/v1/notifications/settings", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async testNotification(channel: string, message?: string) {
    return this.request<any>(`/api/v1/notifications/test/${channel}`, {
      method: "POST",
      body: JSON.stringify({ message: message || "Test notification from CloudGentic Gateway" }),
    });
  }

  // Rule Templates
  async listRuleTemplates() {
    return this.request<{ templates: any[] }>("/api/v1/rules/templates");
  }

  async applyRuleTemplate(templateId: string) {
    return this.request<any[]>(`/api/v1/rules/templates/${templateId}/apply`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  }

  // Agents
  async getAgentsOverview() {
    return this.request<{ agents: any[] }>("/api/v1/agents/overview");
  }

  // Provider Health
  async getProviderHealth() {
    return this.request<any>("/api/v1/health/providers");
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export const api = new ApiClient();

// Types
export interface User {
  id: string;
  email: string;
  display_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  totp_enabled: boolean;
  setup_complete: boolean;
  created_at: string;
}

export interface ConnectedAccount {
  id: string;
  provider: string;
  provider_account_id: string;
  provider_email: string | null;
  display_name: string | null;
  scopes: string[] | null;
  token_expires_at: string | null;
  created_at: string;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  key?: string;
  scopes: Record<string, unknown> | null;
  allowed_providers: string[] | null;
  last_used_at: string | null;
  expires_at: string | null;
  revoked_at: string | null;
  created_at: string;
}

export interface Rule {
  id: string;
  name: string;
  description: string | null;
  rule_type: string;
  conditions: Record<string, unknown>;
  config: Record<string, unknown>;
  priority: number;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  user_id: string | null;
  api_key_id: string | null;
  ip_address: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  provider: string | null;
  status: string;
  detail: string | null;
  request_summary: Record<string, unknown> | null;
}
