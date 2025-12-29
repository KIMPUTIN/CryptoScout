

const API_URL = "https://cryptoscout-production.up.railway.app/projects";

export async function fetchProjects() {
  const response = await fetch(API_URL);
  return response.json();
}