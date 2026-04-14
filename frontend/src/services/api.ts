import axios from 'axios';
import type { ApiResponse, Requirement, Signal, TestCase, LLMConfig } from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
});

// 需求相关 API
export const requirementApi = {
  uploadWord: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<ApiResponse<Requirement[]>>('/requirements/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getRequirements: () =>
    api.get<ApiResponse<Requirement[]>>('/requirements'),
  updateRequirement: (id: string, data: Partial<Requirement>) =>
    api.put<ApiResponse<Requirement>>(`/requirements/${id}`, data),
  deleteRequirement: (id: string) =>
    api.delete<ApiResponse<void>>(`/requirements/${id}`),
  uploadInterfaces: (reqId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<ApiResponse<{ added: number; total: number; signals: string[] }>>(
      `/requirements/${reqId}/interfaces`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
  },
};

// 信号相关 API
export const signalApi = {
  uploadExcel: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<ApiResponse<Signal[]>>('/signals/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getSignals: () =>
    api.get<ApiResponse<Signal[]>>('/signals'),
};

// 测试用例相关 API
export const testCaseApi = {
  generate: (requirementIds: string[]) =>
    api.post<ApiResponse<TestCase[]>>('/testcases/generate', { requirementIds }),
  getTestCases: () =>
    api.get<ApiResponse<TestCase[]>>('/testcases'),
  updateTestCase: (id: string, data: Partial<TestCase>) =>
    api.put<ApiResponse<TestCase>>(`/testcases/${id}`, data),
  deleteTestCase: (id: string) =>
    api.delete<ApiResponse<void>>(`/testcases/${id}`),
  exportExcel: (testCaseIds?: string[]) =>
    api.post('/testcases/export/excel', { ids: testCaseIds }, { responseType: 'blob' }),
  exportWord: (testCaseIds?: string[]) =>
    api.post('/testcases/export/word', { ids: testCaseIds }, { responseType: 'blob' }),
};

// LLM 配置相关 API
export const configApi = {
  getLLMConfig: () =>
    api.get<ApiResponse<LLMConfig>>('/config/llm'),
  updateLLMConfig: (config: LLMConfig) =>
    api.put<ApiResponse<void>>('/config/llm', config),
  testConnection: (config: LLMConfig) =>
    api.post<ApiResponse<{ success: boolean; message: string }>>('/config/llm/test', config),
};

// 健康检查
export const healthApi = {
  check: () => api.get('/health'),
};

// 需求-信号关联 API
export const linkApi = {
  createLinks: (requirementId: string, signalIds: string[]) =>
    api.post<ApiResponse<void>>('/links', { requirementId, signalIds }),
  getLinks: (requirementId: string) =>
    api.get<ApiResponse<{ requirementId: string; signalId: string }[]>>(`/links/${requirementId}`),
  deleteLink: (requirementId: string, signalId: string) =>
    api.delete<ApiResponse<void>>(`/links/${requirementId}/${signalId}`),
};

// 信号库 API
export const signalLibraryApi = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<ApiResponse<{ added: number; updated: number; total: number }>>('/signals/library/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  uploadBatch: (files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    return api.post<ApiResponse<{ added: number; updated: number; total: number }>>('/signals/library/upload-batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getList: (params?: { search?: string; page?: number; pageSize?: number }) =>
    api.get<ApiResponse<{ items: any[]; total: number; page: number; pageSize: number }>>('/signals/library', { params }),
  getByName: (name: string) =>
    api.get<ApiResponse<any>>(`/signals/library/${encodeURIComponent(name)}`),
  getNames: (search?: string) =>
    api.get<ApiResponse<string[]>>('/signals/library/names', { params: { search } }),
};
