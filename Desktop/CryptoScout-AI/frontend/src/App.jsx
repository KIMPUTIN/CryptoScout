import { useEffect, useState, useCallback, useRef } from "react";
import { fetchRanking } from "./api";
import MonitoringDashboard from "./components/MonitoringDashboard";

function App() {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [user, setUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    const categories = ["short-term", "long-term", "low-risk", "high-growth"];
    const [category, setCategory] = useState("short-term");
    
    // Reference for Google Sign-In div
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
            } catch (err) {
                console.error("Failed to parse user data:", err);
                // Clear invalid data
                localStorage.removeItem("token");
                localStorage.removeItem("user");
            }
        }
    }, []);

    // =====================================
    // HANDLE CREDENTIAL RESPONSE
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

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP error! status: ${res.status}`);
            }

            const data = await res.json();

            if (data.token && data.user) {
                localStorage.setItem("token", data.token);
                localStorage.setItem("user", JSON.stringify(data.user));
                setUser(data.user);
                setIsAuthenticated(true);
                
                // Show success message (consider using a toast notification instead)
                console.log("Login successful");
            } else {
                throw new Error("Invalid response from server");
            }
        } catch (err) {
            console.error("Auth error:", err);
            alert(`Authentication error: ${err.message}`);
        }
    }, []);

    // =====================================
    // GOOGLE AUTH SETUP
    // =====================================
    useEffect(() => {
        // Load Google Identity Services script if not already loaded
        if (!window.google) {
            const script = document.createElement('script');
            script.src = 'https://accounts.google.com/gsi/client';
            script.async = true;
            script.defer = true;
            script.onload = initializeGoogleSignIn;
            document.head.appendChild(script);
        } else {
            initializeGoogleSignIn();
        }

        function initializeGoogleSignIn() {
            if (!window.google?.accounts?.id) return;

            const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
            
            if (!clientId) {
                console.error("Google Client ID is not configured");
                return;
            }

            window.google.accounts.id.initialize({
                client_id: clientId,
                callback: handleCredentialResponse,
                auto_select: false,
                cancel_on_tap_outside: true,
            });

            if (googleSignInRef.current) {
                window.google.accounts.id.renderButton(
                    googleSignInRef.current,
                    { 
                        theme: "outline", 
                        size: "large",
                        type: "standard",
                        text: "signin_with",
                        shape: "rectangular",
                        logo_alignment: "left"
                    }
                );
            }
        }

        // Cleanup function
        return () => {
            // Optionally revoke Google Sign-In
            if (window.google?.accounts?.id) {
                window.google.accounts.id.cancel();
            }
        };
    }, [handleCredentialResponse]);

    // =====================================
    // LOAD RANKINGS
    // =====================================
    useEffect(() => {
        let isMounted = true;

        async function load() {
            try {
                setLoading(true);
                setError(null);

                const data = await fetchRanking(category);
                
                if (isMounted) {
                    setProjects(Array.isArray(data) ? data : []);
                }
            } catch (err) {
                console.error("Ranking error:", err);
                if (isMounted) {
                    setError(err.message || "Failed loading rankings");
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        }

        load();

        return () => {
            isMounted = false;
        };
    }, [category]);

    // =====================================
    // LOGOUT FUNCTION
    // =====================================
    const handleLogout = useCallback(() => {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        setUser(null);
        setIsAuthenticated(false);
        
        // Optional: Sign out from Google
        if (window.google?.accounts?.id) {
            window.google.accounts.id.disableAutoSelect();
        }
    }, []);

    // =====================================
    // ADD TO WATCHLIST
    // =====================================
    const handleWatchlist = useCallback(async (symbol) => {
        try {
            const token = localStorage.getItem("token");

            if (!token) {
                alert("Please login first");
                return;
            }

            const response = await fetch(
                `${import.meta.env.VITE_API_URL}/watchlist/add/${encodeURIComponent(symbol)}`,
                {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Content-Type": "application/json",
                    },
                }
            );

            if (!response.ok) {
                if (response.status === 401) {
                    // Token expired or invalid
                    handleLogout();
                    throw new Error("Session expired. Please login again.");
                }
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `Failed adding to watchlist (${response.status})`);
            }

            const data = await response.json();
            alert(data.message || "Added to watchlist successfully");
        } catch (err) {
            console.error("Watchlist error:", err);
            alert(`Could not add to watchlist: ${err.message}`);
        }
    }, [handleLogout]);

    // =====================================
    // UI RENDERING
    // =====================================
    return (
        <div style={{ padding: "20px", fontFamily: "Arial, sans-serif", maxWidth: "1200px", margin: "0 auto" }}>
            <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
                <div>
                    <h1 style={{ margin: 0 }}>🚀 CryptoScout AI</h1>
                    <p style={{ margin: "5px 0 0 0", color: "#666" }}>AI Crypto Discovery Engine</p>
                </div>
                
                <div>
                    {!isAuthenticated ? (
                        <div ref={googleSignInRef} id="googleSignInDiv" />
                    ) : (
                        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                            {user?.picture && (
                                <img 
                                    src={user.picture} 
                                    alt={user.name} 
                                    style={{ width: "32px", height: "32px", borderRadius: "50%" }}
                                />
                            )}
                            <span>{user?.name || "User"}</span>
                            <button 
                                onClick={handleLogout}
                                style={{
                                    padding: "6px 12px",
                                    background: "#dc2626",
                                    color: "white",
                                    border: "none",
                                    borderRadius: "6px",
                                    cursor: "pointer",
                                }}
                            >
                                Logout
                            </button>
                        </div>
                    )}
                </div>
            </header>

            {/* MONITORING DASHBOARD */}
            <MonitoringDashboard />

            {/* LOADING AND ERROR STATES */}
            {loading && (
                <div style={{ textAlign: "center", padding: "40px" }}>
                    <p>Loading projects...</p>
                </div>
            )}
            
            {error && (
                <div style={{ 
                    padding: "15px", 
                    background: "#fee2e2", 
                    color: "#dc2626", 
                    borderRadius: "8px",
                    marginBottom: "20px"
                }}>
                    <strong>Error:</strong> {error}
                    <button 
                        onClick={() => setCategory(category)} // Retrigger load
                        style={{
                            marginLeft: "10px",
                            padding: "4px 8px",
                            background: "#dc2626",
                            color: "white",
                            border: "none",
                            borderRadius: "4px",
                            cursor: "pointer",
                        }}
                    >
                        Retry
                    </button>
                </div>
            )}

            {/* CATEGORY BUTTONS */}
            {!loading && projects.length > 0 && (
                <div style={{ marginBottom: "20px" }}>
                    {categories.map((cat) => (
                        <button
                            key={cat}
                            onClick={() => setCategory(cat)}
                            style={{
                                marginRight: "10px",
                                marginBottom: "10px",
                                padding: "8px 16px",
                                background: category === cat ? "#2563eb" : "#e5e7eb",
                                color: category === cat ? "white" : "#1f2937",
                                border: "none",
                                borderRadius: "6px",
                                cursor: "pointer",
                                fontWeight: category === cat ? "600" : "400",
                                transition: "all 0.2s",
                            }}
                        >
                            {cat.replace("-", " ").toUpperCase()}
                        </button>
                    ))}
                </div>
            )}

            {/* PROJECT CARDS */}
            {!loading && projects.length > 0 ? (
                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
                        gap: "20px",
                    }}
                >
                    {projects.map((project) => (
                        <div
                            key={project.symbol || project.id || Math.random()}
                            style={{
                                border: "1px solid #e5e7eb",
                                borderRadius: "12px",
                                padding: "20px",
                                background: "#ffffff",
                                boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)",
                                transition: "transform 0.2s, box-shadow 0.2s",
                                hover: {
                                    transform: "translateY(-2px)",
                                    boxShadow: "0 10px 15px -3px rgba(0,0,0,0.1)",
                                }
                            }}
                        >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: "10px" }}>
                                <h3 style={{ margin: 0 }}>
                                    {project.name || "Unknown"} 
                                    {project.symbol && <span style={{ color: "#6b7280", fontSize: "0.9em" }}> ({project.symbol})</span>}
                                </h3>
                                {project.market_cap_rank && (
                                    <span style={{ 
                                        background: "#f3f4f6", 
                                        padding: "4px 8px", 
                                        borderRadius: "12px",
                                        fontSize: "0.8em",
                                        color: "#4b5563"
                                    }}>
                                        #{project.market_cap_rank}
                                    </span>
                                )}
                            </div>

                            <div style={{ marginBottom: "15px" }}>
                                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "5px" }}>
                                    <span style={{ color: "#4b5563" }}>Score:</span>
                                    <strong style={{ color: project.score >= 70 ? "#059669" : project.score >= 40 ? "#d97706" : "#dc2626" }}>
                                        {project.score?.toFixed(1) || "N/A"}
                                    </strong>
                                </div>
                                
                                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "5px" }}>
                                    <span style={{ color: "#4b5563" }}>Verdict:</span>
                                    <strong>{project.verdict || "N/A"}</strong>
                                </div>
                                
                                {project.reasons && (
                                    <p style={{ 
                                        color: "#4b5563", 
                                        fontSize: "0.9em", 
                                        marginTop: "10px",
                                        lineHeight: "1.5"
                                    }}>
                                        {project.reasons}
                                    </p>
                                )}
                            </div>

                            <button
                                onClick={() => handleWatchlist(project.symbol)}
                                disabled={!isAuthenticated}
                                style={{
                                    width: "100%",
                                    padding: "10px",
                                    background: !isAuthenticated ? "#d1d5db" : "#2563eb",
                                    color: "white",
                                    border: "none",
                                    borderRadius: "6px",
                                    cursor: !isAuthenticated ? "not-allowed" : "pointer",
                                    fontSize: "0.95em",
                                    fontWeight: "500",
                                    transition: "background 0.2s",
                                }}
                                title={!isAuthenticated ? "Login to add to watchlist" : "Add to watchlist"}
                            >
                                ⭐ {!isAuthenticated ? "Login to Add" : "Add to Watchlist"}
                            </button>
                        </div>
                    ))}
                </div>
            ) : !loading && !error && (
                <div style={{ textAlign: "center", padding: "40px", color: "#6b7280" }}>
                    No projects found for this category.
                </div>
            )}
        </div>
    );
}

export default App;