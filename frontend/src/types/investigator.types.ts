// investigator.types.ts
export interface EvidenceItem {
  source_tool: string;
  finding: string;
}

export interface InvestigationTraceStep {
  step: number;
  tool_name: string;
  tool_input: Record<string, any>;
  tool_result: Record<string, any>;
}

export interface InvestigateRequest {
  objective: string;
}

export interface InvestigateResponseData {
  experiment_id: string;
  objective: string;
  conclusion: string;
  evidence: EvidenceItem[];
  recommendations: string[];
  limitations: string[];
  trace: InvestigationTraceStep[];
  iterations_used: number;
  max_iterations: number;
}
