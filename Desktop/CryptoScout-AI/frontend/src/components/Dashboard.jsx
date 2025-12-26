


import { useEffect, useState } from "react";
import { fetchProjects } from "../api";
import ProjectCard from "./ProjectCard";

export default function Dashboard() {
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    fetchProjects().then(setProjects);
  }, []);

  return (
    <div className="dashboard">
      {projects.map(p => (
        <ProjectCard key={p.id} project={p} />
      ))}
    </div>
  );
}