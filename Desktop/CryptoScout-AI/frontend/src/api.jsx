
const API_BASE = "https://cryptoscout-production.up.railway.app";

export async function fetchRanking(type) {
  console.log("Fetching:", type);

  const res = await fetch(`${API_BASE}/rankings/${type}`);

  console.log("Status:", res.status);

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  const data = await res.json(); // <-- SAFE PARSER

  console.log("Parsed data:", data);

  return data;
}

