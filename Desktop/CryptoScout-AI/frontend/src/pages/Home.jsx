
import { useEffect, useState, useCallback, useRef } from "react";
import { fetchRanking } from "../api";
import { motion, AnimatePresence } from "framer-motion";

function Home() {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [user, setUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    const categories = ["short-term", "long-term", "low-risk", "high-growth"];
    const [category, setCategory] = useState("short-term");

    const googleSignInRef = useRef(null);

    const [expandedSymbol, setExpandedSymbol] = useState(null);
    const [explanations, setExplanations] = useState({});

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
    // FETCH FUNCTION
    // =====================================

    const fetchExplanation = async (symbol) => {
    try {
        const res = await fetch(
            `${import.meta.env.VITE_API_URL}/ai/explain/${symbol}`
        );
        const data = await res.json();

        setExplanations(prev => ({
            ...prev,
            [symbol]: data.explanation
        }));

    } catch {
        setExplanations(prev => ({
            ...prev,
            [symbol]: "Unable to generate explanation."
        }));
    }
};



    // =====================================
    // UI
    // =====================================
    return (
        <div
            style={{
                minHeight: "100vh",
                background: "radial-gradient(circle at 20% 20%, #1e293b, #0f172a)",
                padding: "40px 24px",
                fontFamily: "'Inter', sans-serif",
                color: "#f8fafc"
            }}
        >
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
                    /*Project card container */
                    {projects.map((project) => (
                        <div
                            key={project.symbol}
                            style={{
                                backdropFilter: "blur(14px)",
                                background: "rgba(255, 255, 255, 0.05)",
                                border: "1px solid rgba(255,255,255,0.08)",
                                borderRadius: "18px",
                                padding: "22px",
                                boxShadow: "0 8px 30px rgba(0,0,0,0.4)",
                                transition: "all 0.3s ease",
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
                                        padding: "6px 12px",
                                        borderRadius: "20px",
                                        fontSize: "0.75rem",
                                        fontWeight: "600",
                                        background:
                                            project.ai_verdict === "BUY"
                                                ? "rgba(16,185,129,0.15)"
                                                : project.ai_verdict === "SELL"
                                                ? "rgba(239,68,68,0.15)"
                                                : "rgba(245,158,11,0.15)",
                                        color:
                                            project.ai_verdict === "BUY"
                                                ? "#10b981"
                                                : project.ai_verdict === "SELL"
                                                ? "#ef4444"
                                                : "#f59e0b",
                                        border: "1px solid rgba(255,255,255,0.08)"
                                    }}
                                >
                                    {project.ai_verdict || "N/A"}
                                </span>

                            </div>


                            {/* Score Meter */}
                            <div style={{ marginTop: "15px" }}>
                                <div
                                    style={{
                                        height: "8px",
                                        background: "rgba(255,255,255,0.08)",
                                        borderRadius: "10px",
                                        overflow: "hidden",
                                    }}
                                >
                                    <div
                                        style={{
                                            width: `${project.combined_score * 100}%`,
                                            background:
                                                project.combined_score >= 0.5
                                                    ? "#10b981"
                                                    : project.combined_score >= 0.3
                                                    ? "#f59e0b"
                                                    : "#ef4444",
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
                                        color: "#94a3b8",
                                    }}
                                >
                                    <span>Score</span>
                                    <strong
                                        style={{
                                            fontSize: "1.2rem",
                                            fontWeight: "700",
                                            background:
                                                project.ai_score >= 70
                                                    ? "linear-gradient(135deg,#10b981,#059669)"
                                                    : project.ai_score >= 40
                                                    ? "linear-gradient(135deg,#f59e0b,#d97706)"
                                                    : "linear-gradient(135deg,#ef4444,#dc2626)",
                                            WebkitBackgroundClip: "text",
                                            WebkitTextFillColor: "transparent",
                                        }}
                                    >
                                        {project.ai_score?.toFixed(1) || "N/A"}
                                    </strong>
                                </div>
                            </div>


                            {/* Explanation */}
                            <motion.button
                                whileHover={{ scale: 1.03 }}
                                whileTap={{ scale: 0.97 }}
                                onClick={() => {
                                    if (!explanations[project.symbol]) {
                                        fetchExplanation(project.symbol);
                                    }
                                    setExpandedSymbol(
                                        expandedSymbol === project.symbol ? null : project.symbol
                                    );
                                }}
                                style={{
                                    marginTop: "12px",
                                    background: "linear-gradient(135deg, #1e3a8a, #2563eb)",
                                    color: "white",
                                    border: "none",
                                    padding: "8px 14px",
                                    borderRadius: "10px",
                                    cursor: "pointer",
                                    fontSize: "0.85rem",
                                    fontWeight: "500",
                                    boxShadow: "0 4px 10px rgba(37,99,235,0.3)"
                                }}
                            >
                                🧠 Why Trending
                            </motion.button>

                            <AnimatePresence>
                                {expandedSymbol === project.symbol && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: "auto", opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.35, ease: "easeInOut" }}
                                        style={{
                                            overflow: "hidden",
                                            marginTop: "12px",
                                            borderRadius: "16px",
                                            background: "rgba(255,255,255,0.04)",
                                            backdropFilter: "blur(12px)",
                                            border: "1px solid rgba(255,255,255,0.06)",
                                            padding: "0 16px",
                                        }}
                                    >
                                        <motion.div
                                            whileHover={{ y: -4 }}
                                            transition={{ type: "spring", stiffness: 120 }}
                                            style={{
                                                padding: "16px 0",
                                                fontSize: "0.9rem",
                                                color: "#cbd5e1",
                                                lineHeight: "1.6"
                                            }}
                                        >
                                            {explanations[project.symbol] || "Generating explanation..."}
                                        </motion.div>
                                    </motion.div>
                                )}
                            </AnimatePresence>


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
                                            {project.volatility_heat || "LOW"}
                                        </strong>
                                    </div>

                                    <div>
                                        Trend Momentum:{" "}
                                        <strong>
                                            {project.trend_momentum
                                                ? (project.trend_momentum * 100).toFixed(2)
                                                : "0.00"}%
                                        </strong>
                                    </div>
                                </div>

                                <button
                                    onClick={() => handleWatchlist(project.symbol)}
                                    style={{
                                        marginTop: "15px",
                                        width: "100%",
                                        padding: "10px",
                                        background: "#2563eb",
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