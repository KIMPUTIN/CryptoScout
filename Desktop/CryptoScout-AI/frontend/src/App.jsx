
import { useEffect, useState } from "react";
import { fetchRanking } from "./api";
import MonitoringDashboard from "./components/MonitoringDashboard";

function App() {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const categories = ["short-term", "long-term", "low-risk", "high-growth"];
    const [category, setCategory] = useState("short-term");

    // =====================================
    // LOAD RANKINGS
    // =====================================
    useEffect(() => {
        async function load() {
            try {
                setLoading(true);
                setError(null);

                const data = await fetchRanking(category);
                setProjects(data);
            } catch (err) {
                console.error("Ranking error:", err);
                setError("Failed loading rankings");
            } finally {
                setLoading(false);
            }
        }

        load();
    }, [category]);

    // =====================================
    // GOOGLE AUTH SETUP
    // =====================================
    useEffect(() => {
        if (!window.google) return;

        window.google.accounts.id.initialize({
            client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
            callback: handleCredentialResponse,
        });

        window.google.accounts.id.renderButton(
            document.getElementById("googleSignInDiv"),
            { theme: "outline", size: "large" }
        );
    }, []);

    async function handleCredentialResponse(response) {
        try {
            const token = response.credential;

            const res = await fetch(
                `${import.meta.env.VITE_API_URL}/auth/google`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ token }),
                }
            );

            const data = await res.json();

            if (data.token) {
                localStorage.setItem("token", data.token);
                localStorage.setItem("user", JSON.stringify(data.user));
                alert("Login successful");
            } else {
                alert("Login failed");
            }
        } catch (err) {
            console.error("Auth error:", err);
            alert("Authentication error");
        }
    }

    // =====================================
    // ADD TO WATCHLIST
    // =====================================
    async function handleWatchlist(symbol) {
        try {
            const token = localStorage.getItem("token");

            if (!token) {
                alert("Please login first");
                return;
            }

            const res = await fetch(
                `${import.meta.env.VITE_API_URL}/watchlist/add/${symbol}`,
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!res.ok) {
                throw new Error("Failed adding to watchlist");
            }

            alert("Added to watchlist");
        } catch (err) {
            console.error("Watchlist error:", err);
            alert("Could not add to watchlist");
        }
    }

    // =====================================
    // UI
    // =====================================
    return (
        <div style={{ padding: "20px", fontFamily: "Arial" }}>
            <h1>🚀 CryptoScout AI</h1>
            <p>AI Crypto Discovery Engine</p>

            <div id="googleSignInDiv" style={{ marginBottom: "20px" }} />

            {/* ================= MONITOR DASHBOARD ================= */}
            <MonitoringDashboard />

            {loading && <p>Loading projects...</p>}
            {error && <p style={{ color: "red" }}>{error}</p>}

            {/* CATEGORY BUTTONS */}
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
                            cursor: "pointer",
                        }}
                    >
                        {cat.replace("-", " ").toUpperCase()}
                    </button>
                ))}
            </div>

            {/* PROJECT CARDS */}
            <div
                style={{
                    display: "grid",
                    gridTemplateColumns:
                        "repeat(auto-fill, minmax(250px, 1fr))",
                    gap: "20px",
                }}
            >
                {projects.map((project) => (
                    <div
                        key={project.symbol}
                        style={{
                            border: "1px solid #e0e0e0",
                            borderRadius: "10px",
                            padding: "20px",
                            background: "#ffffff",
                            boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
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

                        <button
                            onClick={() =>
                                handleWatchlist(project.symbol)
                            }
                        >
                            ⭐ Add to Watchlist
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default App;
