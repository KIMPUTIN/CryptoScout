


export default function ProjectCard({ project }) {
  return (
    <div className="card">
      <h3>{project.name} ({project.symbol})</h3>
      <p>Score: {project.score}</p>
      <p>Verdict: {project.verdict}</p>
      <p>{project.reasons}</p>
      {project.website && (
        <a href={project.website} target="_blank">Website</a>
      )}
    </div>
  );
}