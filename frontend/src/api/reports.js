import api from './apiClient';

export async function generateReport(projectId) {
  const { data } = await api.post('/reports/generate', { project_id: projectId });
  return data;
}

export async function getProjectReports(projectId) {
  const { data } = await api.get(`/projects/${projectId}/reports`);
  return data;
}
