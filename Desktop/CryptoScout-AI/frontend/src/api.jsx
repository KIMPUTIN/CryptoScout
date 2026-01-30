

const API_BASE = "https://cryptoscout-production.up.railway.app";

/
export async function fetchProjects() {
  const response = await fetch(`${API_BASE}/projects`);
  return response.json();
}
/

export async function fetchRanking(type) {
  const res = await fetch(`${API_BASE}/rankings/${type}`);
  
  if (!res.ok) {
    throw new Error("Ranking fetch failed");
  }
  return res.json();
}


