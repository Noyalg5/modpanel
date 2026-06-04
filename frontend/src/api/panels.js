import api from './apiClient';

export async function getPanels() {
  const { data } = await api.get('/panels');
  return data;
}
