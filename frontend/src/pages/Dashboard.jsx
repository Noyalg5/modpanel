import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProjects } from '../api/projects';
import { getProjectOptimisations } from '../api/optimiser';
import Badge from '../components/Badge';
import Spinner from '../components/Spinner';

export default function Dashboard() {
  const [projects, setProjects] = useState([]);
  const [allRuns, setAllRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    async function load() {
      try {
        const projectList = await getProjects();
        setProjects(projectList);
        const runArrays = await Promise.all(
          projectList.map((p) => getProjectOptimisations(p.id).catch(() => []))
        );
        setAllRuns(runArrays.flat());
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const sortedRuns = [...allRuns].sort(
    (a, b) => new Date(b.created_at) - new Date(a.created_at)
  );
  const latestWaste = sortedRuns[0]?.waste_percentage ?? null;

  const recentProjects = [...projects]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5);

  if (loading) return <Spinner />;

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">ModPanel AI Platform overview</p>
        </div>
        <button
          onClick={() => navigate('/projects')}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700"
        >
          + New Project
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
        <StatCard label="Total Projects" value={projects.length} colour="blue" />
        <StatCard label="Optimisation Runs" value={allRuns.length} colour="indigo" />
        <StatCard
          label="Latest Waste %"
          value={latestWaste !== null ? `${latestWaste.toFixed(1)}%` : '—'}
          colour="green"
        />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="px-5 py-4 border-b border-gray-100 flex justify-between items-center">
          <h2 className="font-semibold text-gray-900">Recent Projects</h2>
          <button
            onClick={() => navigate('/projects')}
            className="text-sm text-blue-600 hover:underline"
          >
            View all
          </button>
        </div>
        {recentProjects.length === 0 ? (
          <p className="p-8 text-center text-gray-400 text-sm">
            No projects yet.{' '}
            <button
              onClick={() => navigate('/projects')}
              className="text-blue-600 hover:underline"
            >
              Create your first one →
            </button>
          </p>
        ) : (
          <ul className="divide-y divide-gray-50">
            {recentProjects.map((p) => (
              <li
                key={p.id}
                onClick={() => navigate(`/projects/${p.id}`)}
                className="px-5 py-3.5 flex items-center justify-between hover:bg-gray-50 cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <span className="font-medium text-gray-900 text-sm">{p.name}</span>
                  {p.location && (
                    <span className="text-xs text-gray-400">{p.location}</span>
                  )}
                  <Badge status={p.status} />
                </div>
                <span className="text-xs text-gray-400">
                  {new Date(p.created_at).toLocaleDateString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, colour }) {
  const colours = {
    blue: 'text-blue-600 bg-blue-50',
    indigo: 'text-indigo-600 bg-indigo-50',
    green: 'text-green-600 bg-green-50',
  };
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-3xl font-bold mt-1 ${colours[colour] ?? ''} rounded-lg px-2 py-0.5 inline-block`}>
        {value}
      </p>
    </div>
  );
}
