

const API_URL = "https://your-railway-backend-url/projects";

export async function fetchProjects() {
  const res = await fetch(API_URL);
  return res.json();
}