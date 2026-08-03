import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/services/health.service";
import type { HealthData } from "@/types/api.types";

export function useHealth() {
  return useQuery<HealthData | null, Error>({
    queryKey: ["health"],
    queryFn: async () => {
      const response = await getHealth();
      return response.data;
    },
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}
