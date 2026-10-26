import { Route, Routes } from "react-router-dom";

import { AppLayout, RouteGuard } from "@/components/layout";
import { DashboardPage } from "@/routes/DashboardPage";
import { ExamFormPage } from "@/routes/ExamFormPage";
import { LoginPage } from "@/routes/LoginPage";
import { MasterDrugsPage, MasterIcd10Page } from "@/routes/MasterPages";
import { NotFoundPage } from "@/routes/NotFoundPage";
import { PatientDetailPage } from "@/routes/PatientDetailPage";
import { PatientNewPage } from "@/routes/PatientNewPage";
import { PatientsPage } from "@/routes/PatientsPage";
import { PipelineLogsPage } from "@/routes/PipelineLogsPage";

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<RouteGuard />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />

          {/* Fase 2: RME dasar */}
          <Route path="/patients" element={<PatientsPage />} />
          <Route path="/patients/new" element={<PatientNewPage />} />
          <Route path="/patients/:id" element={<PatientDetailPage />} />
          <Route path="/encounters/:id/exam" element={<ExamFormPage />} />
          <Route path="/exam" element={<PatientsPage mode="exam" />} />

          {/* Master data */}
          <Route path="/master/icd10" element={<MasterIcd10Page />} />
          <Route path="/master/drugs" element={<MasterDrugsPage />} />

          {/* Fase 6: evaluasi */}
          <Route path="/pipeline-logs" element={<PipelineLogsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
