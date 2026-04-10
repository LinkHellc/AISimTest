import { create } from 'zustand';
import type { Requirement, Signal, TestCase, GenerationProgress } from '../types';

interface AppState {
  // 需求相关
  requirements: Requirement[];
  selectedRequirementIds: string[];
  setRequirements: (requirements: Requirement[]) => void;
  toggleRequirementSelection: (id: string) => void;
  selectAllRequirements: () => void;
  clearRequirementSelection: () => void;

  // 信号相关
  signals: Signal[];
  setSignals: (signals: Signal[]) => void;

  // 测试用例相关
  testCases: TestCase[];
  setTestCases: (testCases: TestCase[]) => void;
  updateTestCase: (id: string, data: Partial<TestCase>) => void;
  removeTestCase: (id: string) => void;

  // 生成进度
  generationProgress: GenerationProgress;
  setGenerationProgress: (progress: Partial<GenerationProgress>) => void;
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
}));
