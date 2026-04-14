// 需求条目
export interface Requirement {
  id: string;
  title: string;
  signalInterfaces: { name: string; type: 'Input' | 'Output' }[];  // 信号接口列表
  sceneDescription: string;     // 场景描述
  functionDescription: string;  // 功能描述
  entryCondition: string;       // 功能触发条件
  executionBody: string;        // 功能进入后执行
  exitCondition: string;        // 功能退出条件
  postExitBehavior: string;    // 功能退出后执行
  testModel: string;           // 测试模型名称（用户填写）
  testUnitModel: string;      // 测试单元模型名称（用户填写）
}

// 信号定义
export interface Signal {
  id: string;
  name: string;
  messageId: string | null;
  startBit: number;
  length: number;
  factor: number;
  offset: number;
  minValue: number;
  maxValue: number;
  unit: string;
  busType: 'CAN' | 'LIN';
  classType: string;       // Input / Output / Parameter
  dataType: string;        // 数据类型
  description: string;     // 描述
}

// 需求-信号关联
export interface RequirementSignalLink {
  requirementId: string;
  signalIds: string[];
}

// 测试用例
export interface TestCase {
  id: string;
  name: string;
  requirementId: string;
  precondition: string;
  steps: (string | TestStep)[];
  expectedResult: string;
  category: 'positive' | 'negative';
  signals: Signal[];
}

export interface TestStep {
  TestStepName: string;
  TestStepAction: string;
  TestTransition?: string;
  TestNextStepName?: string;
  TestVerifyName?: string;
  WhenCondition?: string;
  TestVerify?: string;
  TestDescription?: string;
}

// LLM 配置
export interface LLMConfig {
  provider: string;
  apiKey: string;
  baseUrl: string;
  model: string;
  temperature: number;
  maxTokens: number;
}

// 生成参数
export interface GenerationParams {
  requirements: Requirement[];
  signals: Signal[];
  includeNegative: boolean;
}

// API 响应
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// 文件上传状态
export type UploadStatus = 'idle' | 'uploading' | 'parsing' | 'success' | 'error';

// 生成进度
export interface GenerationProgress {
  current: number;
  total: number;
  status: 'idle' | 'generating' | 'completed' | 'error';
  currentRequirement: string;
}
