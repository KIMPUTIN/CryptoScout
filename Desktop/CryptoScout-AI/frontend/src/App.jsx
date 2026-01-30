import { useEffect, useState } from "react";
import { fetchProjects } from "./api";

function App() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadProjects() {
      try {
        const data = await fetchProjects();
        setProjects(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load projects");
      } finally {
        setLoading(false);
      }
    }

    loadProjects();
  }, []);

  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1>🚀 CryptoScout AI</h1>
      <p>AI Crypto Discovery Engine</p>

      {loading && <p>Loading projects...</p>}

      {error && <p style={{ color: "red" }}>{error}</p>}

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


