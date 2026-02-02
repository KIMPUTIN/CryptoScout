
const API_BASE = "https://cryptoscout-production.up.railway.app";

console.log("API TEST VERSION 2"); // <--- ADD THIS

export async function fetchRanking(type) {
  console.log("Fetching:", type);

  const res = await fetch(`${API_BASE}/rankings/${type}`);

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  const data = await res.json();

  console.log("Parsed data:", data);

  return data;
}

