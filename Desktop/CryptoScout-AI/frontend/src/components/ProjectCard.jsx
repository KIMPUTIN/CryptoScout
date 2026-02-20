


export default function ProjectCard({ project }) {
  return (
    <div className="card">
      <h3>{project.name} ({project.symbol})</h3>
      <p>Score: {project.combined_score ?? 0}</p>
      <p>Verdict: {project.ai_verdict ?? "UNKNOWN"}</p>
      <p>{project.reasons}</p>
      {project.website && (
        <a href={project.website} target="_blank" rel="noreferrer">Website</a>
      )}
    </div>
  );
}