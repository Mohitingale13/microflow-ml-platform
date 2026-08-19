// investigator.service.ts
import { post } from './api';
import type { ApiResponse } from '@/types/api.types';
import type { InvestigateRequest, InvestigateResponseData } from '@/types/investigator.types';

export async function postInvestigate(
  experimentId: string,
  payload: InvestigateRequest
): Promise<ApiResponse<InvestigateResponseData>> {
  const response = await post<InvestigateResponseData>(
    `/experiments/${experimentId}/investigate`,
    payload
  );
  return response;
}
