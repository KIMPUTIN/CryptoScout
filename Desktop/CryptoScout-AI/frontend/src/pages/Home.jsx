
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
                                background: "var(--bg-card)",
                                border: "1px solid var(--border-color)",
                                borderRadius: "16px",
                                padding: "20px",
                                transition: "all 0.2s ease",
                            }}
                        >
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <h3>
                                    {project.name}
                                    <span style={{ color: "var(--text-secondary)" }}>
                                        {" "}({project.symbol})
                                    </span>
                                </h3>

                                <span
                                    style={{
                                        background:
                                            project.ai_verdict === "STRONG BUY"
                                                ? "var(--accent-green)"
                                                : project.ai_verdict === "BUY"
                                                ? "var(--accent-blue)"
                                                : project.ai_verdict === "HOLD"
                                                ? "var(--accent-orange)"
                                                : "var(--accent-red)",
                                        padding: "4px 10px",
                                        borderRadius: "20px",
                                        fontSize: "0.75rem",
                                        fontWeight: "600",
                                    }}
                                >
                                    {project.ai_verdict}
                                </span>
                            </div>


                            {/* Score Meter */}
                            <div style={{ marginTop: "15px" }}>
                                <div
                                    style={{
                                        height: "8px",
                                        background: "var(--border-color)",
                                        borderRadius: "10px",
                                        overflow: "hidden",
                                    }}
                                >
                                    <div
                                        style={{
                                            width: `${project.combined_score * 100}%`,
                                            background:
                                                project.combined_score >= 0.7
                                                    ? "var(--accent-green)"
                                                    : project.combined_score >= 0.4
                                                    ? "var(--accent-orange)"
                                                    : "var(--accent-red)",
                                            height: "100%",
                                            transition: "width 0.3s ease",
                                        }}
                                    />
                                </div>

                                <div
                                    style={{
                                        display: "flex",
                                        justifyContent: "space-between",
                                        marginTop: "6px",
                                        fontSize: "0.85rem",
                                        color: "var(--text-secondary)",
                                    }}
                                >
                                    <span>Score</span>
                                    <strong>
                                        {(project.combined_score * 100).toFixed(1)}
                                    </strong>
                                </div>
                            </div>


                            {/* Volatility + Momentum */}
                                <div style={{ marginTop: "15px", fontSize: "0.85rem" }}>
                                    <div>
                                        Volatility:{" "}
                                        <strong
                                            style={{
                                                color:
                                                    project.volatility_heat === "EXTREME"
                                                        ? "var(--accent-red)"
                                                        : project.volatility_heat === "HIGH"
                                                        ? "var(--accent-orange)"
                                                        : "var(--accent-green)",
                                            }}
                                        >
                                            {project.volatility_heat}
                                        </strong>
                                    </div>

                                    <div>
                                        Trend Momentum:{" "}
                                        <strong>
                                            {(project.trend_momentum * 100).toFixed(2)}%
                                        </strong>
                                    </div>
                                </div>

                                <button
                                    onClick={() => handleWatchlist(project.symbol)}
                                    style={{
                                        marginTop: "15px",
                                        width: "100%",
                                        padding: "10px",
                                        background: "var(--accent-blue)",
                                        border: "none",
                                        borderRadius: "8px",
                                        fontWeight: "600",
                                        cursor: "pointer",
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