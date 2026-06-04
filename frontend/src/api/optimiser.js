import api from './apiClient';

export async function runOptimisation(payload) {
  const { data } = await api.post('/optimiser/run', payload);
  return data;
}

export async function getOptimisationRun(runId) {
  const { data } = await api.get(`/optimiser/${runId}`);
  return data;
}

export async function getProjectOptimisations(projectId) {
  const { data } = await api.get(`/projects/${projectId}/optimisations`);
  return data;
}

export async function compareOptimisation(payload) {
  const { data } = await api.post('/optimiser/compare', payload);
  return data;
}

export async function getCarbonEstimate(runId) {
  const { data } = await api.get(`/optimiser/${runId}/carbon`);
  return data;
}
