import { useEffect, useState } from "react";
import { fetchProjects } from "./api";

function App() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const categories = [
  "short-term",
  "long-term",
  "low-risk",
  "high-growth"
];
  const [category, setCategory] = useState("short-term");


  useEffect(() => {
  async function load() {
    try {
      setLoading(true);
      const data = await fetchRanking(category);
      setProjects(data);
    } catch {
      setError("Failed loading rankings");
    } finally {
      setLoading(false);
    }
  }

  load();
}, [category]);


  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1>🚀 CryptoScout AI</h1>
      <p>AI Crypto Discovery Engine</p>

      {loading && <p>Loading projects...</p>}

      {error && <p style={{ color: "red" }}>{error}</p>}

      <div style={{ marginBottom: "20px" }}>
      {categories.map((cat) => (
        <button
        key={cat}
        onClick={() => setCategory(cat)}
        style={{
          marginRight: "10px",
          padding: "8px 12px",
          background: category === cat ? "#2563eb" : "#ddd",
          color: category === cat ? "white" : "black",
          border: "none",
          borderRadius: "6px",
          cursor: "pointer"
        }}
        >
          {cat.replace("-", " ").toUpperCase()}
        </button>
        ))}
      </div>


      <div
       style={{ 
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))",
        gap: "20px",
        marginTop: "20px",
      }}
    >
        {projects.map((project, index) => (
          <div
            key={index}
            style={{ /**/
              border: "1px solid #e0e0e0",
              borderRadius: "10px",
              padding: "20px",
              background: "#ffffff",
              boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
              transition: "0.2s",
            }}
          >
            <h3>
              {project.name} ({project.symbol})
            </h3>

            <p>
              <strong>Score:</strong> {project.score}
            </p>

            <p>
              <strong>Verdict:</strong> {project.verdict}
            </p>

            <p>{project.reasons}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;


