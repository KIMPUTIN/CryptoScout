
const API_BASE = "https://cryptoscout-production.up.railway.app";

console.log("API TEST VERSION 2"); // <--- ADD THIS

export async function fetchRanking(type) {
  try {
    const url = `${API_BASE}/rankings/${type}`;

    console.log("📡 Fetching:", url);

    const res = await fetch(url);

    console.log("📥 Status:", res.status);

    const text = await res.text();

    console.log("📄 Raw:", text);

    if (!res.ok) {
      throw new Error("HTTP " + res.status);
    }

    return JSON.parse(text);

  } catch (err) {
    console.error("❌ API ERROR:", err);
    throw err;
  }
}


