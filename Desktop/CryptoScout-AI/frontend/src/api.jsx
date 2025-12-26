

const API_URL = "https://cryptoscout-production.up.railway.app";

export async function fetchProjects() {
  const res = await fetch(API_URL);
  return res.json();
}