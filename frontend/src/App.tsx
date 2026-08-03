import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppLayout } from "@/layouts/AppLayout";
import { Dashboard } from "@/pages/Dashboard";
import { Datasets } from "@/pages/Datasets";
import { DatasetDetail } from "@/pages/DatasetDetail";
import { Experiments } from "@/pages/Experiments";
import { ExperimentDetail } from "@/pages/ExperimentDetail";
import { RunDetail } from "@/pages/RunDetail";
import { Training } from "@/pages/Training";
import { Artifacts } from "@/pages/Artifacts";
import { Metrics } from "@/pages/Metrics";
import { Pipeline } from "@/pages/Pipeline";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="datasets" element={<Datasets />} />
            <Route path="datasets/:id" element={<DatasetDetail />} />
            <Route path="experiments" element={<Experiments />} />
            <Route path="experiments/:id" element={<ExperimentDetail />} />
            <Route path="runs/:id" element={<RunDetail />} />
            <Route path="training" element={<Training />} />
            <Route path="artifacts" element={<Artifacts />} />
            <Route path="metrics" element={<Metrics />} />
            <Route path="pipeline" element={<Pipeline />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
