import { create } from 'zustand';
import type { Requirement, Signal, TestCase, GenerationProgress } from '../types';

export interface RequirementInterface {
  id: string;
  requirementId: string;
  interfaceName: 'Input' | 'Output';
  signalName: string;
  description: string;
  sourceDoc: string;
}

export interface SignalLibraryItem {
  id: string;
  name: string;
  description: string;
  dataType: string;
  unit: string;
  valueTable: string;
  initialValue: string;
  bus: string;
  storageClass: string;
  dimension: string;
  factor: number;
  offset: number;
  minValue: number | null;
  maxValue: number | null;
  sourceFile: string;
}

interface AppState {
  // 需求相关
  requirements: Requirement[];
  selectedRequirementIds: string[];
  setRequirements: (requirements: Requirement[]) => void;
  toggleRequirementSelection: (id: string) => void;
  selectAllRequirements: () => void;
  clearRequirementSelection: () => void;

  // 需求接口相关
  requirementInterfaces: RequirementInterface[];
  setRequirementInterfaces: (interfaces: RequirementInterface[]) => void;
  addRequirementInterface: (iface: RequirementInterface) => void;

  // 信号相关
  signals: Signal[];
  setSignals: (signals: Signal[]) => void;

  // 信号库相关
  signalLibrary: SignalLibraryItem[];
  setSignalLibrary: (signals: SignalLibraryItem[]) => void;

  // 测试用例相关
  testCases: TestCase[];
  setTestCases: (testCases: TestCase[]) => void;
  updateTestCase: (id: string, data: Partial<TestCase>) => void;
  removeTestCase: (id: string) => void;

  // 生成进度
  generationProgress: GenerationProgress;
  setGenerationProgress: (progress: Partial<GenerationProgress>) => void;

  // 上传进度
  uploadProgress: {
    uploading: boolean;
    progress: number;
    statusText: string;
    logs: { time: string; text: string }[];
  };
  setUploadProgress: (progress: Partial<{ uploading?: boolean; progress?: number; statusText?: string; log?: string; clearLogs?: boolean }>) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // 需求相关
  requirements: [],
  selectedRequirementIds: [],
  setRequirements: (requirements) => set({ requirements }),
  toggleRequirementSelection: (id) =>
    set((state) => ({
      selectedRequirementIds: state.selectedRequirementIds.includes(id)
        ? state.selectedRequirementIds.filter((rid) => rid !== id)
        : [...state.selectedRequirementIds, id],
    })),
  selectAllRequirements: () =>
    set((state) => ({
      selectedRequirementIds: state.requirements.map((r) => r.id),
    })),
  clearRequirementSelection: () => set({ selectedRequirementIds: [] }),

  // 信号相关
  signals: [],
  setSignals: (signals) => set({ signals }),

  // 需求接口相关
  requirementInterfaces: [],
  setRequirementInterfaces: (interfaces) => set({ requirementInterfaces: interfaces }),
  addRequirementInterface: (iface) =>
    set((state) => ({ requirementInterfaces: [...state.requirementInterfaces, iface] })),

  // 信号库相关
  signalLibrary: [],
  setSignalLibrary: (signals) => set({ signalLibrary: signals }),

  // 测试用例相关
  testCases: [],
  setTestCases: (testCases) => set({ testCases }),
  updateTestCase: (id, data) =>
    set((state) => ({
      testCases: state.testCases.map((tc) =>
        tc.id === id ? { ...tc, ...data } : tc
      ),
    })),
  removeTestCase: (id) =>
    set((state) => ({
      testCases: state.testCases.filter((tc) => tc.id !== id),
    })),

  // 生成进度
  generationProgress: {
    current: 0,
    total: 0,
    status: 'idle',
    currentRequirement: '',
  },
  setGenerationProgress: (progress) =>
    set((state) => ({
      generationProgress: { ...state.generationProgress, ...progress },
    })),

  // 上传进度
  uploadProgress: {
    uploading: false,
    progress: 0,
    statusText: '',
    logs: [],
  },
  setUploadProgress: (progress) =>
    set((state) => {
      if ('clearLogs' in progress && progress.clearLogs) {
        return {
          uploadProgress: {
            ...state.uploadProgress,
            logs: [],
          },
        };
      }
      if ('log' in progress && progress.log) {
        return {
          uploadProgress: {
            ...state.uploadProgress,
            ...progress,
            logs: [
              ...state.uploadProgress.logs,
              { time: new Date().toLocaleTimeString(), text: progress.log as string },
            ],
          },
        };
      }
      return {
        uploadProgress: { ...state.uploadProgress, ...progress },
      };
    }),
}));
