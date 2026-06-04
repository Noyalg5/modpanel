import api from './apiClient';

export async function generateQuote(projectId, runId) {
  const { data } = await api.post('/quotes/generate', {
    project_id: projectId,
    optimisation_run_id: runId,
  });
  return data;
}

export async function getProjectQuotes(projectId) {
  const { data } = await api.get(`/projects/${projectId}/quotes`);
  return data;
}
