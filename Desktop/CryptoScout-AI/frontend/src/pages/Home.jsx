
import { useEffect, useState, useCallback, useRef } from "react";
import { fetchRanking } from "../api";

function Home() {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [user, setUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    const categories = ["short-term", "long-term", "low-risk", "high-growth"];
    const [category, setCategory] = useState("short-term");

    const googleSignInRef = useRef(null);

    // =====================================
    // CHECK EXISTING SESSION
    // =====================================
    useEffect(() => {
        const token = localStorage.getItem("token");
        const savedUser = localStorage.getItem("user");

        if (token && savedUser) {
            try {
                setUser(JSON.parse(savedUser));
                setIsAuthenticated(true);
            } catch {
                localStorage.removeItem("token");
                localStorage.removeItem("user");
            }
        }
    }, []);

    // =====================================
    // GOOGLE LOGIN
    // =====================================
    const handleCredentialResponse = useCallback(async (response) => {
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

            if (!res.ok) throw new Error("Authentication failed");

            const data = await res.json();

            localStorage.setItem("token", data.access_token);
            localStorage.setItem("user", JSON.stringify(data.user));
            setUser(data.user);
            setIsAuthenticated(true);

        } catch (err) {
            alert("Login failed");
        }
    }, []);

    useEffect(() => {
        if (!window.google) {
            const script = document.createElement("script");
            script.src = "https://accounts.google.com/gsi/client";
            script.async = true;
            script.onload = initializeGoogle;
            document.head.appendChild(script);
        } else {
            initializeGoogle();
        }

        function initializeGoogle() {
            const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
            if (!clientId) return;

            window.google.accounts.id.initialize({
                client_id: clientId,
                callback: handleCredentialResponse,
            });

            if (googleSignInRef.current) {
                window.google.accounts.id.renderButton(
                    googleSignInRef.current,
                    { theme: "outline", size: "large" }
                );
            }
        }
    }, [handleCredentialResponse]);

    // =====================================
    // LOAD RANKINGS
    // =====================================
    useEffect(() => {
        async function load() {
            try {
                setLoading(true);
                setError(null);

                const data = await fetchRanking(category);
                setProjects(Array.isArray(data) ? data : []);

            } catch (err) {
                setError("Failed loading rankings");
            } finally {
                setLoading(false);
            }
        }

        load();
    }, [category]);

    // =====================================
    // LOGOUT
    // =====================================
    const handleLogout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        setUser(null);
        setIsAuthenticated(false);
    };

    // =====================================
    // WATCHLIST
    // =====================================
    const handleWatchlist = async (symbol) => {
        try {
            const token = localStorage.getItem("token");
            if (!token) return alert("Please login first");

            const res = await fetch(
                `${import.meta.env.VITE_API_URL}/watchlist/add/${symbol}`,
                {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${token}`,
                    },
                }
            );

            if (!res.ok) throw new Error();

            alert("Added to watchlist");

        } catch {
            alert("Could not add to watchlist");
        }
    };

    // =====================================
    // UI
    // =====================================
    return (
        <div style={{ padding: "20px", maxWidth: "1200px", margin: "0 auto" }}>
            <header style={{ display: "flex", justifyContent: "space-between", marginBottom: "20px" }}>
                <div>
                    <h1>🚀 CryptoScout AI</h1>
                    <p style={{ color: "#666" }}>AI Crypto Discovery Engine</p>
                </div>

                {!isAuthenticated ? (
                    <div ref={googleSignInRef}></div>
                ) : (
                    <div>
                        <span>{user?.name}</span>
                        <button onClick={handleLogout} style={{ marginLeft: "10px" }}>
                            Logout
                        </button>
                    </div>
                )}
            </header>

            {/* CATEGORY BUTTONS */}
            <div style={{ marginBottom: "20px" }}>
                {categories.map((cat) => (
                    <button
                        key={cat}
                        onClick={() => setCategory(cat)}
                        style={{
                            marginRight: "10px",
                            padding: "8px 16px",
                            background: category === cat ? "#2563eb" : "#e5e7eb",
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

            {loading && <p>Loading...</p>}
            {error && <p style={{ color: "red" }}>{error}</p>}

            {!loading && (
                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
                        gap: "20px",
                    }}
                >
                    {projects.map((project) => (
                        <div
                            key={project.symbol}
                            style={{
                                border: "1px solid #e5e7eb",
                                borderRadius: "12px",
                                padding: "20px",
                                background: "#fff",
                            }}
                        >
                            <h3>
                                {project.name} ({project.symbol})
                            </h3>

                            <p>
                                <strong>Score:</strong>{" "}
                                {project.combined_score !== undefined
                                    ? (project.combined_score * 100).toFixed(1)
                                    : "N/A"}
                            </p>

                            <p>
                                <strong>Verdict:</strong>{" "}
                                {project.ai_verdict || "N/A"}
                            </p>

                            <button
                                onClick={() => handleWatchlist(project.symbol)}
                                disabled={!isAuthenticated}
                                style={{
                                    marginTop: "10px",
                                    width: "100%",
                                    padding: "8px",
                                    background: isAuthenticated ? "#2563eb" : "#ccc",
                                    color: "white",
                                    border: "none",
                                    borderRadius: "6px",
                                }}
                            >
                                ⭐ Add to Watchlist
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default Home;