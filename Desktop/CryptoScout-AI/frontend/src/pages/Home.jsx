
import { useEffect, useState, useCallback, useRef } from "react";
import { fetchRanking } from "../api";
import { motion, AnimatePresence } from "framer-motion";

function Home() {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [user, setUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [activeView, setActiveView] = useState("discover"); // discover, watchlist, portfolio, analytics

    const categories = ["short-term", "long-term", "low-risk", "high-growth"];
    const [category, setCategory] = useState("short-term");

    const googleSignInRef = useRef(null);

    const [expandedSymbol, setExpandedSymbol] = useState(null);
    const [explanations, setExplanations] = useState({});
    const [watchlist, setWatchlist] = useState([]);

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
                fetchWatchlist();
            } catch {
                localStorage.removeItem("token");
                localStorage.removeItem("user");
            }
        }
    }, []);

    // =====================================
    // FETCH WATCHLIST
    // =====================================
    const fetchWatchlist = async () => {
        try {
            const token = localStorage.getItem("token");
            if (!token) return;

            const res = await fetch(`${import.meta.env.VITE_API_URL}/watchlist`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            
            if (res.ok) {
                const data = await res.json();
                setWatchlist(data);
            }
        } catch (error) {
            console.error("Failed to fetch watchlist");
        }
    };

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
            fetchWatchlist();

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
        setWatchlist([]);
    };

    // =====================================
    // WATCHLIST
    // =====================================
    const handleWatchlist = async (symbol) => {
        try {
            const token = localStorage.getItem("token");
            if (!token) return alert("Please login first");

            const isInWatchlist = watchlist.some(item => item.symbol === symbol);
            const endpoint = isInWatchlist ? 'remove' : 'add';

            const res = await fetch(
                `${import.meta.env.VITE_API_URL}/watchlist/${endpoint}/${symbol}`,
                {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${token}`,
                    },
                }
            );

            if (!res.ok) throw new Error();

            alert(isInWatchlist ? "Removed from watchlist" : "Added to watchlist");
            fetchWatchlist();

        } catch {
            alert("Could not update watchlist");
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
    // DASHBOARD STATS
    // =====================================
    const getDashboardStats = () => {
        const totalProjects = projects.length;
        const avgScore = projects.reduce((acc, p) => acc + (p.ai_score || 0), 0) / totalProjects || 0;
        const buySignals = projects.filter(p => p.ai_verdict === "BUY").length;
        const highVolatility = projects.filter(p => p.volatility_heat === "EXTREME" || p.volatility_heat === "HIGH").length;
        
        return { totalProjects, avgScore, buySignals, highVolatility };
    };

    const stats = getDashboardStats();

    // =====================================
    // UI
    // =====================================
    return (
        <div style={{
            display: "flex",
            minHeight: "100vh",
            background: "#0f172a",
            fontFamily: "'Inter', sans-serif",
            color: "#f8fafc"
        }}>
            <style>{`
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
                
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                .sidebar {
                    background: rgba(15, 23, 42, 0.95);
                    backdrop-filter: blur(10px);
                    border-right: 1px solid rgba(255,255,255,0.08);
                    transition: width 0.3s ease;
                    height: 100vh;
                    position: sticky;
                    top: 0;
                    overflow-y: auto;
                }

                .sidebar::-webkit-scrollbar {
                    width: 4px;
                }

                .sidebar::-webkit-scrollbar-track {
                    background: rgba(255,255,255,0.02);
                }

                .sidebar::-webkit-scrollbar-thumb {
                    background: rgba(255,255,255,0.1);
                    border-radius: 4px;
                }

                .sidebar.collapsed {
                    width: 80px;
                }

                .sidebar.expanded {
                    width: 280px;
                }

                .nav-item {
                    display: flex;
                    align-items: center;
                    padding: 12px 20px;
                    margin: 4px 12px;
                    border-radius: 12px;
                    cursor: pointer;
                    transition: all 0.2s;
                    color: #94a3b8;
                }

                .nav-item:hover {
                    background: rgba(255,255,255,0.05);
                    color: white;
                }

                .nav-item.active {
                    background: linear-gradient(135deg, #2563eb, #1d4ed8);
                    color: white;
                }

                .nav-item.collapsed {
                    justify-content: center;
                    padding: 12px;
                }

                .stat-card {
                    background: rgba(255,255,255,0.03);
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 16px;
                    padding: 20px;
                    transition: transform 0.2s;
                }

                .stat-card:hover {
                    transform: translateY(-4px);
                    background: rgba(255,255,255,0.05);
                }

                .category-chip {
                    padding: 8px 16px;
                    background: rgba(255,255,255,0.03);
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 20px;
                    cursor: pointer;
                    transition: all 0.2s;
                    color: #94a3b8;
                }

                .category-chip:hover {
                    background: rgba(37,99,235,0.1);
                    border-color: #2563eb;
                    color: white;
                }

                .category-chip.active {
                    background: #2563eb;
                    border-color: #2563eb;
                    color: white;
                }

                .project-card {
                    background: rgba(255,255,255,0.03);
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 24px;
                    padding: 24px;
                    transition: all 0.3s;
                }

                .project-card:hover {
                    transform: translateY(-4px);
                    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
                    border-color: rgba(37,99,235,0.3);
                }

                .btn-primary {
                    background: linear-gradient(135deg, #2563eb, #1d4ed8);
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 12px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .btn-primary:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 20px rgba(37,99,235,0.3);
                }

                .btn-outline {
                    background: transparent;
                    border: 1px solid rgba(255,255,255,0.1);
                    color: #94a3b8;
                    padding: 8px 16px;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .btn-outline:hover {
                    border-color: #2563eb;
                    color: white;
                }
            `}</style>

            {/* SIDEBAR */}
            <motion.div 
                className={`sidebar ${sidebarCollapsed ? 'collapsed' : 'expanded'}`}
                initial={false}
                animate={{ width: sidebarCollapsed ? 80 : 280 }}
                transition={{ duration: 0.3 }}
            >
                {/* Logo */}
                <div style={{ 
                    padding: sidebarCollapsed ? "20px 0" : "24px 20px",
                    textAlign: sidebarCollapsed ? "center" : "left",
                    borderBottom: "1px solid rgba(255,255,255,0.08)"
                }}>
                    {sidebarCollapsed ? (
                        <span style={{ fontSize: "24px" }}>🚀</span>
                    ) : (
                        <h2 style={{ fontSize: "1.5rem", background: "linear-gradient(135deg, #60a5fa, #2563eb)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                            CryptoScout AI
                        </h2>
                    )}
                </div>

                {/* Toggle Button */}
                <div style={{ padding: "16px 12px", textAlign: "right" }}>
                    <button 
                        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                        className="btn-outline"
                        style={{ padding: "8px 12px" }}
                    >
                        {sidebarCollapsed ? "→" : "←"}
                    </button>
                </div>

                {/* Navigation */}
                <nav style={{ marginTop: "20px" }}>
                    {[
                        { icon: "🔍", label: "Discover", view: "discover" },
                        { icon: "⭐", label: "Watchlist", view: "watchlist" },
                        { icon: "📊", label: "Portfolio", view: "portfolio" },
                        { icon: "📈", label: "Analytics", view: "analytics" },
                    ].map((item) => (
                        <div
                            key={item.view}
                            className={`nav-item ${activeView === item.view ? 'active' : ''} ${sidebarCollapsed ? 'collapsed' : ''}`}
                            onClick={() => setActiveView(item.view)}
                        >
                            <span style={{ fontSize: "20px", marginRight: sidebarCollapsed ? 0 : "12px" }}>
                                {item.icon}
                            </span>
                            {!sidebarCollapsed && <span>{item.label}</span>}
                        </div>
                    ))}
                </nav>

                {/* User Section */}
                {!sidebarCollapsed && (
                    <div style={{ 
                        position: "absolute",
                        bottom: "20px",
                        left: "20px",
                        right: "20px"
                    }}>
                        {!isAuthenticated ? (
                            <div ref={googleSignInRef}></div>
                        ) : (
                            <div style={{ 
                                background: "rgba(255,255,255,0.03)",
                                borderRadius: "12px",
                                padding: "16px"
                            }}>
                                <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px" }}>
                                    <div style={{
                                        width: "40px",
                                        height: "40px",
                                        borderRadius: "20px",
                                        background: "linear-gradient(135deg, #2563eb, #1d4ed8)",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        fontSize: "20px"
                                    }}>
                                        {user?.name?.charAt(0) || "U"}
                                    </div>
                                    <div>
                                        <div style={{ fontWeight: "600" }}>{user?.name || "User"}</div>
                                        <div style={{ fontSize: "12px", color: "#94a3b8" }}>{watchlist.length} in watchlist</div>
                                    </div>
                                </div>
                                <button 
                                    onClick={handleLogout}
                                    className="btn-outline"
                                    style={{ width: "100%" }}
                                >
                                    Logout
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </motion.div>

            {/* MAIN CONTENT */}
            <div style={{ 
                flex: 1,
                padding: "32px",
                overflowY: "auto",
                height: "100vh"
            }}>
                {/* Header */}
                <div style={{ 
                    display: "flex", 
                    justifyContent: "space-between", 
                    alignItems: "center",
                    marginBottom: "32px"
                }}>
                    <div>
                        <h1 style={{ fontSize: "2rem", marginBottom: "8px" }}>
                            {activeView === "discover" && "🔍 Discover Projects"}
                            {activeView === "watchlist" && "⭐ Your Watchlist"}
                            {activeView === "portfolio" && "📊 Portfolio Tracker"}
                            {activeView === "analytics" && "📈 Market Analytics"}
                        </h1>
                        <p style={{ color: "#94a3b8" }}>
                            {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                        </p>
                    </div>

                    {isAuthenticated && sidebarCollapsed && (
                        <div ref={googleSignInRef}></div>
                    )}
                </div>

                {/* Dashboard Stats (only show for discover view) */}
                {activeView === "discover" && !loading && !error && (
                    <div style={{ 
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                        gap: "20px",
                        marginBottom: "32px"
                    }}>
                        <div className="stat-card">
                            <div style={{ color: "#94a3b8", marginBottom: "8px" }}>Total Projects</div>
                            <div style={{ fontSize: "2rem", fontWeight: "700" }}>{stats.totalProjects}</div>
                        </div>
                        <div className="stat-card">
                            <div style={{ color: "#94a3b8", marginBottom: "8px" }}>Avg AI Score</div>
                            <div style={{ fontSize: "2rem", fontWeight: "700", color: "#10b981" }}>
                                {stats.avgScore.toFixed(1)}
                            </div>
                        </div>
                        <div className="stat-card">
                            <div style={{ color: "#94a3b8", marginBottom: "8px" }}>Buy Signals</div>
                            <div style={{ fontSize: "2rem", fontWeight: "700", color: "#2563eb" }}>{stats.buySignals}</div>
                        </div>
                        <div className="stat-card">
                            <div style={{ color: "#94a3b8", marginBottom: "8px" }}>High Volatility</div>
                            <div style={{ fontSize: "2rem", fontWeight: "700", color: "#ef4444" }}>{stats.highVolatility}</div>
                        </div>
                    </div>
                )}

                {/* Category Filters (only for discover view) */}
                {activeView === "discover" && (
                    <div style={{ 
                        display: "flex", 
                        gap: "10px", 
                        marginBottom: "32px",
                        flexWrap: "wrap"
                    }}>
                        {categories.map((cat) => (
                            <button
                                key={cat}
                                className={`category-chip ${category === cat ? 'active' : ''}`}
                                onClick={() => setCategory(cat)}
                            >
                                {cat.replace("-", " ").toUpperCase()}
                            </button>
                        ))}
                    </div>
                )}

                {/* Content based on active view */}
                {activeView === "discover" && (
                    <>
                        {loading && (
                            <div style={{ textAlign: "center", padding: "60px" }}>
                                <div style={{ fontSize: "48px", marginBottom: "20px" }}>🔄</div>
                                <p style={{ color: "#94a3b8" }}>Loading projects...</p>
                            </div>
                        )}
                        
                        {error && (
                            <div style={{ 
                                textAlign: "center", 
                                padding: "40px",
                                background: "rgba(239,68,68,0.1)",
                                borderRadius: "16px"
                            }}>
                                <p style={{ color: "#ef4444" }}>{error}</p>
                                <button 
                                    onClick={() => setCategory(category)}
                                    className="btn-primary"
                                    style={{ marginTop: "16px" }}
                                >
                                    Try Again
                                </button>
                            </div>
                        )}

                        {!loading && !error && (
                            <div
                                style={{
                                    display: "grid",
                                    gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))",
                                    gap: "24px",
                                }}
                            >
                                {projects.map((project) => {
                                    const isInWatchlist = watchlist.some(item => item.symbol === project.symbol);
                                    
                                    return (
                                        <motion.div
                                            key={project.symbol}
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ duration: 0.3 }}
                                            className="project-card"
                                        >
                                            <div style={{ 
                                                display: "flex", 
                                                justifyContent: "space-between", 
                                                alignItems: "flex-start",
                                                marginBottom: "16px"
                                            }}>
                                                <div>
                                                    <h3 style={{ fontSize: "1.2rem", marginBottom: "4px" }}>
                                                        {project.name}
                                                    </h3>
                                                    <span style={{ color: "#94a3b8", fontSize: "0.9rem" }}>
                                                        {project.symbol}
                                                    </span>
                                                </div>

                                                <span
                                                    style={{
                                                        padding: "6px 12px",
                                                        borderRadius: "20px",
                                                        fontSize: "0.75rem",
                                                        fontWeight: "600",
                                                        background: project.ai_verdict === "BUY"
                                                            ? "rgba(16,185,129,0.15)"
                                                            : project.ai_verdict === "SELL"
                                                            ? "rgba(239,68,68,0.15)"
                                                            : "rgba(245,158,11,0.15)",
                                                        color: project.ai_verdict === "BUY"
                                                            ? "#10b981"
                                                            : project.ai_verdict === "SELL"
                                                            ? "#ef4444"
                                                            : "#f59e0b"
                                                    }}
                                                >
                                                    {project.ai_verdict || "HOLD"}
                                                </span>
                                            </div>

                                            {/* Score */}
                                            <div style={{ marginBottom: "16px" }}>
                                                <div style={{ 
                                                    display: "flex", 
                                                    justifyContent: "space-between",
                                                    marginBottom: "8px",
                                                    color: "#94a3b8",
                                                    fontSize: "0.9rem"
                                                }}>
                                                    <span>AI Confidence</span>
                                                    <span style={{ 
                                                        color: project.ai_score >= 70 ? "#10b981" : 
                                                               project.ai_score >= 40 ? "#f59e0b" : "#ef4444",
                                                        fontWeight: "600"
                                                    }}>
                                                        {project.ai_score?.toFixed(1) || "0.0"}%
                                                    </span>
                                                </div>
                                                <div style={{
                                                    height: "6px",
                                                    background: "rgba(255,255,255,0.08)",
                                                    borderRadius: "3px",
                                                    overflow: "hidden"
                                                }}>
                                                    <motion.div
                                                        initial={{ width: 0 }}
                                                        animate={{ width: `${project.ai_score || 0}%` }}
                                                        transition={{ duration: 0.8 }}
                                                        style={{
                                                            height: "100%",
                                                            background: project.ai_score >= 70
                                                                ? "linear-gradient(90deg, #10b981, #059669)"
                                                                : project.ai_score >= 40
                                                                ? "linear-gradient(90deg, #f59e0b, #d97706)"
                                                                : "linear-gradient(90deg, #ef4444, #dc2626)",
                                                            borderRadius: "3px"
                                                        }}
                                                    />
                                                </div>
                                            </div>

                                            {/* Metrics */}
                                            <div style={{ 
                                                display: "grid",
                                                gridTemplateColumns: "1fr 1fr",
                                                gap: "12px",
                                                marginBottom: "16px",
                                                padding: "12px",
                                                background: "rgba(0,0,0,0.2)",
                                                borderRadius: "12px"
                                            }}>
                                                <div>
                                                    <div style={{ color: "#94a3b8", fontSize: "0.8rem", marginBottom: "4px" }}>
                                                        Volatility
                                                    </div>
                                                    <span style={{
                                                        color: project.volatility_heat === "EXTREME" ? "#ef4444" :
                                                               project.volatility_heat === "HIGH" ? "#f97316" : "#10b981",
                                                        fontWeight: "600"
                                                    }}>
                                                        {project.volatility_heat || "LOW"}
                                                    </span>
                                                </div>
                                                <div>
                                                    <div style={{ color: "#94a3b8", fontSize: "0.8rem", marginBottom: "4px" }}>
                                                        Momentum
                                                    </div>
                                                    <span style={{ color: "#60a5fa", fontWeight: "600" }}>
                                                        {project.trend_momentum
                                                            ? `${(project.trend_momentum * 100).toFixed(1)}%`
                                                            : "0.0%"}
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Actions */}
                                            <div style={{ display: "flex", gap: "10px" }}>
                                                <button
                                                    onClick={() => {
                                                        if (!explanations[project.symbol]) {
                                                            fetchExplanation(project.symbol);
                                                        }
                                                        setExpandedSymbol(
                                                            expandedSymbol === project.symbol ? null : project.symbol
                                                        );
                                                    }}
                                                    className="btn-outline"
                                                    style={{ flex: 1 }}
                                                >
                                                    {explanations[project.symbol] ? "📝 Hide" : "🧠 Analyze"}
                                                </button>
                                                <button
                                                    onClick={() => handleWatchlist(project.symbol)}
                                                    className="btn-primary"
                                                    style={{ flex: 1 }}
                                                >
                                                    {isInWatchlist ? "⭐ Added" : "⭐ Add"}
                                                </button>
                                            </div>

                                            {/* Explanation */}
                                            <AnimatePresence>
                                                {expandedSymbol === project.symbol && (
                                                    <motion.div
                                                        initial={{ height: 0, opacity: 0 }}
                                                        animate={{ height: "auto", opacity: 1 }}
                                                        exit={{ height: 0, opacity: 0 }}
                                                        transition={{ duration: 0.3 }}
                                                        style={{
                                                            overflow: "hidden",
                                                            marginTop: "16px"
                                                        }}
                                                    >
                                                        <div style={{
                                                            padding: "16px",
                                                            background: "rgba(255,255,255,0.02)",
                                                            borderRadius: "12px",
                                                            border: "1px solid rgba(255,255,255,0.05)",
                                                            fontSize: "0.9rem",
                                                            color: "#cbd5e1",
                                                            lineHeight: "1.6"
                                                        }}>
                                                            {explanations[project.symbol] || "Generating AI analysis..."}
                                                        </div>
                                                    </motion.div>
                                                )}
                                            </AnimatePresence>
                                        </motion.div>
                                    );
                                })}
                            </div>
                        )}
                    </>
                )}

                {/* Watchlist View */}
                {activeView === "watchlist" && (
                    <div>
                        {watchlist.length === 0 ? (
                            <div style={{ 
                                textAlign: "center", 
                                padding: "60px",
                                background: "rgba(255,255,255,0.02)",
                                borderRadius: "24px"
                            }}>
                                <div style={{ fontSize: "48px", marginBottom: "20px" }}>⭐</div>
                                <h3 style={{ marginBottom: "12px" }}>Your watchlist is empty</h3>
                                <p style={{ color: "#94a3b8", marginBottom: "24px" }}>
                                    Start adding projects to track them here
                                </p>
                                <button 
                                    onClick={() => setActiveView("discover")}
                                    className="btn-primary"
                                >
                                    Discover Projects
                                </button>
                            </div>
                        ) : (
                            <div style={{
                                display: "grid",
                                gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
                                gap: "20px"
                            }}>
                                {watchlist.map((item) => (
                                    <div key={item.symbol} className="project-card">
                                        <h3>{item.name} ({item.symbol})</h3>
                                        <p style={{ color: "#94a3b8", marginTop: "8px" }}>
                                            Added on {new Date(item.added_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Portfolio View (Placeholder) */}
                {activeView === "portfolio" && (
                    <div style={{ 
                        textAlign: "center", 
                        padding: "60px",
                        background: "rgba(255,255,255,0.02)",
                        borderRadius: "24px"
                    }}>
                        <div style={{ fontSize: "48px", marginBottom: "20px" }}>📊</div>
                        <h3 style={{ marginBottom: "12px" }}>Portfolio Tracker Coming Soon</h3>
                        <p style={{ color: "#94a3b8" }}>
                            Track your crypto investments and performance
                        </p>
                    </div>
                )}

                {/* Analytics View (Placeholder) */}
                {activeView === "analytics" && (
                    <div style={{ 
                        textAlign: "center", 
                        padding: "60px",
                        background: "rgba(255,255,255,0.02)",
                        borderRadius: "24px"
                    }}>
                        <div style={{ fontSize: "48px", marginBottom: "20px" }}>📈</div>
                        <h3 style={{ marginBottom: "12px" }}>Market Analytics Coming Soon</h3>
                        <p style={{ color: "#94a3b8" }}>
                            Advanced charts and market insights
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default Home;