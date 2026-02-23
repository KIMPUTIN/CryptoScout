
// src/components/ProtectedRoute.jsx

import { Navigate } from "react-router-dom";

export default function ProtectedRoute({ children }) {
    const user = JSON.parse(localStorage.getItem("user"));

    if (!user) {
        return <Navigate to="/" />;
    }

    if (user.email !== "your@email.com") {
        return <div>Unauthorized</div>;
    }

    return children;
}