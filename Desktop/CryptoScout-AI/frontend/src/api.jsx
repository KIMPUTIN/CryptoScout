

const API_BASE = "https://cryptoscout-production.up.railway.app";

export async function fetchProjects() {
  const response = await fetch(`${API_BASE}/projects`);
  return response.json();
}