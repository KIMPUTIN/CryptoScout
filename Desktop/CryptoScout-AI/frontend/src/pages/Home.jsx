
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

        if (!window.google) {
            const script = document.createElement("script");
            script.src = "https://accounts.google.com/gsi/client";
            script.async = true;
            script.onload = initializeGoogle;
            document.head.appendChild(script);
        } else {
            initializeGoogle();
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
    // FETCH EXPLANATION
    // =====================================
    const fetchExplanation = useCallback(async (symbol) => {
        try {
            const res = await fetch(
                `${import.meta.env.VITE_API_URL}/ai/explain/${symbol}`
            );
            const data = await res.json();

            setExplanations(prev => ({
                ...prev,
                [symbol]: data.explanation || "No explanation available."
            }));
        } catch {
            setExplanations(prev => ({
                ...prev,
                [symbol]: "Unable to generate explanation."
            }));
        }
    }, []);

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
            <style>{`
                .text-secondary {
                    color: #94a3b8;
                }
                .accent-red {
                    color: #ef4444;
                }
                .accent-orange {
                    color: #f97316;
                }
                .accent-green {
                    color: #10b981;
                }
                .watchlist-btn {
                    background: linear-gradient(135deg, #2563eb, #1d4ed8);
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 8px;
                    font-weight: 600;
                    cursor: pointer;
                    width: 100%;
                    transition: transform 0.2s;
                }
                .watchlist-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 20px rgba(37, 99, 235, 0.4);
                }
            `}</style>

            <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "40px" }}>
                <div>
                    <h1 style={{ fontSize: "2rem", margin: 0 }}>🚀 CryptoScout AI</h1>
                    <p style={{ color: "#94a3b8", margin: "5px 0 0" }}>AI Crypto Discovery Engine</p>
                </div>

                {!isAuthenticated ? (
                    <div ref={googleSignInRef}></div>
                ) : (
                    <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
                        <span style={{ color: "#94a3b8" }}>Welcome, {user?.name}</span>
                        <button 
                            onClick={handleLogout}
                            style={{
                                padding: "8px 16px",
                                background: "rgba(239, 68, 68, 0.1)",
                                color: "#ef4444",
                                border: "1px solid rgba(239, 68, 68, 0.3)",
                                borderRadius: "6px",
                                cursor: "pointer",
                                fontWeight: "500"
                            }}
                        >
                            Logout
                        </button>
                    </div>
                )}
            </header>

            {/* CATEGORY BUTTONS */}
            <div style={{ marginBottom: "30px", display: "flex", gap: "10px", flexWrap: "wrap" }}>
                {categories.map((cat) => (
                    <motion.button
                        key={cat}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => setCategory(cat)}
                        style={{
                            padding: "10px 20px",
                            background: category === cat ? "#2563eb" : "rgba(255,255,255,0.05)",
                            color: category === cat ? "white" : "#94a3b8",
                            border: category === cat ? "none" : "1px solid rgba(255,255,255,0.1)",
                            borderRadius: "8px",
                            cursor: "pointer",
                            fontWeight: "600",
                            fontSize: "0.9rem",
                            textTransform: "uppercase",
                            letterSpacing: "0.5px"
                        }}
                    >
                        {cat.replace("-", " ")}
                    </motion.button>
                ))}
            </div>

            {loading && (
                <div style={{ textAlign: "center", padding: "50px" }}>
                    <p style={{ color: "#94a3b8" }}>Loading rankings...</p>
                </div>
            )}
            
            {error && (
                <div style={{ textAlign: "center", padding: "30px", background: "rgba(239,68,68,0.1)", borderRadius: "12px" }}>
                    <p style={{ color: "#ef4444" }}>{error}</p>
                </div>
            )}

            {!loading && !error && (
                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
                        gap: "24px",
                    }}
                >
                    {projects.map((project) => (
                        <motion.div
                            key={project.symbol}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3 }}
                            style={{
                                backdropFilter: "blur(14px)",
                                background: "rgba(255, 255, 255, 0.03)",
                                border: "1px solid rgba(255,255,255,0.08)",
                                borderRadius: "24px",
                                padding: "24px",
                                boxShadow: "0 8px 30px rgba(0,0,0,0.4)",
                                transition: "all 0.3s ease",
                            }}
                        >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "15px" }}>
                                <div>
                                    <h3 style={{ margin: 0, fontSize: "1.2rem" }}>
                                        {project.name}
                                        <span style={{ color: "#94a3b8", fontSize: "0.9rem", marginLeft: "5px" }}>
                                            ({project.symbol})
                                        </span>
                                    </h3>
                                </div>

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
                                    {project.ai_verdict || "HOLD"}
                                </span>
                            </div>

                            {/* Score Meter */}
                            <div style={{ marginTop: "20px" }}>
                                <div
                                    style={{
                                        height: "8px",
                                        background: "rgba(255,255,255,0.08)",
                                        borderRadius: "10px",
                                        overflow: "hidden",
                                    }}
                                >
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${(project.combined_score || 0) * 100}%` }}
                                        transition={{ duration: 0.8, delay: 0.2 }}
                                        style={{
                                            background: (project.combined_score || 0) >= 0.7
                                                ? "linear-gradient(90deg, #10b981, #059669)"
                                                : (project.combined_score || 0) >= 0.4
                                                ? "linear-gradient(90deg, #f59e0b, #d97706)"
                                                : "linear-gradient(90deg, #ef4444, #dc2626)",
                                            height: "100%",
                                            borderRadius: "10px",
                                        }}
                                    />
                                </div>

                                <div
                                    style={{
                                        display: "flex",
                                        justifyContent: "space-between",
                                        marginTop: "8px",
                                        fontSize: "0.85rem",
                                        color: "#94a3b8",
                                    }}
                                >
                                    <span>AI Confidence Score</span>
                                    <strong
                                        style={{
                                            fontSize: "1.2rem",
                                            fontWeight: "700",
                                            color: (project.ai_score || 0) >= 70
                                                ? "#10b981"
                                                : (project.ai_score || 0) >= 40
                                                ? "#f59e0b"
                                                : "#ef4444",
                                        }}
                                    >
                                        {project.ai_score?.toFixed(1) || "0.0"}
                                    </strong>
                                </div>
                            </div>

                            {/* Volatility + Momentum */}
                            <div style={{ 
                                marginTop: "20px", 
                                fontSize: "0.9rem",
                                display: "grid",
                                gridTemplateColumns: "1fr 1fr",
                                gap: "15px",
                                background: "rgba(0,0,0,0.2)",
                                padding: "15px",
                                borderRadius: "12px"
                            }}>
                                <div>
                                    <div style={{ color: "#94a3b8", marginBottom: "5px" }}>Volatility</div>
                                    <strong
                                        style={{
                                            color: project.volatility_heat === "EXTREME"
                                                ? "#ef4444"
                                                : project.volatility_heat === "HIGH"
                                                ? "#f97316"
                                                : "#10b981",
                                            fontSize: "1rem"
                                        }}
                                    >
                                        {project.volatility_heat || "LOW"}
                                    </strong>
                                </div>

                                <div>
                                    <div style={{ color: "#94a3b8", marginBottom: "5px" }}>Momentum</div>
                                    <strong style={{ color: "#60a5fa", fontSize: "1rem" }}>
                                        {project.trend_momentum
                                            ? `${(project.trend_momentum * 100).toFixed(1)}%`
                                            : "0.0%"}
                                    </strong>
                                </div>
                            </div>

                            {/* Explanation Button */}
                            <motion.button
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => {
                                    if (!explanations[project.symbol]) {
                                        fetchExplanation(project.symbol);
                                    }
                                    setExpandedSymbol(
                                        expandedSymbol === project.symbol ? null : project.symbol
                                    );
                                }}
                                style={{
                                    marginTop: "15px",
                                    width: "100%",
                                    background: "linear-gradient(135deg, #1e3a8a, #2563eb)",
                                    color: "white",
                                    border: "none",
                                    padding: "12px",
                                    borderRadius: "12px",
                                    cursor: "pointer",
                                    fontSize: "0.9rem",
                                    fontWeight: "500",
                                    boxShadow: "0 4px 10px rgba(37,99,235,0.3)"
                                }}
                            >
                                🧠 {explanations[project.symbol] ? "Hide Analysis" : "Show AI Analysis"}
                            </motion.button>

                            <AnimatePresence>
                                {expandedSymbol === project.symbol && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: "auto", opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.3 }}
                                        style={{
                                            overflow: "hidden",
                                            marginTop: "15px",
                                        }}
                                    >
                                        <div
                                            style={{
                                                padding: "16px",
                                                background: "rgba(255,255,255,0.04)",
                                                borderRadius: "12px",
                                                border: "1px solid rgba(255,255,255,0.06)",
                                                fontSize: "0.9rem",
                                                color: "#cbd5e1",
                                                lineHeight: "1.6"
                                            }}
                                        >
                                            {explanations[project.symbol] || "Generating analysis..."}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            {/* Watchlist Button */}
                            <motion.button
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => handleWatchlist(project.symbol)}
                                className="watchlist-btn"
                                style={{
                                    marginTop: "15px",
                                    background: "linear-gradient(135deg, #2563eb, #1d4ed8)",
                                    color: "white",
                                    border: "none",
                                    padding: "12px",
                                    borderRadius: "12px",
                                    fontWeight: "600",
                                    cursor: "pointer",
                                    width: "100%"
                                }}
                            >
                                ⭐ Add to Watchlist
                            </motion.button>
                        </motion.div>
                    ))}
                </div>
            )}

            {!loading && !error && projects.length === 0 && (
                <div style={{ textAlign: "center", padding: "50px", background: "rgba(255,255,255,0.02)", borderRadius: "16px" }}>
                    <p style={{ color: "#94a3b8" }}>No projects found for this category.</p>
                </div>
            )}
        </div>
    );
}

export default Home;