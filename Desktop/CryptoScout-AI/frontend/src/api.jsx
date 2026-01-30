
const API_BASE = "https://cryptoscout-production.up.railway.app";

export async function fetchRanking(type) {
  try {
    console.log("Fetching:", type);

    const res = await fetch(`${API_BASE}/rankings/${type}`);

    console.log("Status:", res.status);

    const text = await res.text();

    console.log("Raw response:", text);

    const data = JSON.parse(text);

    return data;

  } catch (err) {
    console.error("API ERROR:", err);
    throw err;
  }
}






/
const API_BASE = "https:**cryptoscout-production.up.railway.app";


export async function fetchProjects() {
  const response = await fetch(`${API_BASE}/projects`);
  return response.json();
}






export async function fetchRanking(type) {
  const res = await fetch(`${API_BASE}/rankings/${type}`);
  
  if (!res.ok) {
    throw new Error("Ranking fetch failed");
  }
  return res.json();
}
/

