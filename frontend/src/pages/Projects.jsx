import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProjects, createProject } from '../api/projects';
import Badge from '../components/Badge';
import Modal from '../components/Modal';
import Spinner from '../components/Spinner';
import ErrorMessage from '../components/ErrorMessage';

const EMPTY_FORM = { name: '', description: '', location: '', status: 'draft' };

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => { fetchProjects(); }, []);

  async function fetchProjects() {
    try {
      setProjects(await getProjects());
    } finally {
      setLoading(false);
    }
  }

  function openModal() {
    setForm(EMPTY_FORM);
    setError('');
    setModalOpen(true);
  }

  async function handleCreate(e) {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await createProject(form);
      setModalOpen(false);
      fetchProjects();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create project');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <Spinner />;

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
        <button
          onClick={openModal}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700"
        >
          + Create Project
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
          <p className="text-gray-400 mb-3">No projects yet.</p>
          <button onClick={openModal} className="text-blue-600 hover:underline text-sm">
            Create your first project →
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} onClick={() => navigate(`/projects/${p.id}`)} />
          ))}
        </div>
      )}

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Create Project">
        <form onSubmit={handleCreate} className="space-y-3">
          <Field label="Name *">
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="input"
              required
              autoFocus
            />
          </Field>
          <Field label="Location">
            <input
              value={form.location}
              onChange={(e) => setForm({ ...form, location: e.target.value })}
              className="input"
            />
          </Field>
          <Field label="Description">
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="input resize-none"
              rows={3}
            />
          </Field>
          <Field label="Status">
            <select
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
              className="input"
            >
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="complete">Complete</option>
            </select>
          </Field>
          <ErrorMessage message={error} onDismiss={() => setError('')} />
          <div className="flex justify-end gap-3 pt-1">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1.5"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="bg-blue-600 text-white text-sm px-4 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? 'Creating…' : 'Create'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

function ProjectCard({ project: p, onClick }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex flex-col">
      <div className="flex justify-between items-start mb-2">
        <h2 className="font-semibold text-gray-900">{p.name}</h2>
        <Badge status={p.status} />
      </div>
      {p.location && <p className="text-xs text-gray-500 mb-1">{p.location}</p>}
      {p.description && (
        <p className="text-sm text-gray-600 mb-3 line-clamp-2 flex-1">{p.description}</p>
      )}
      <div className="mt-auto pt-3 flex justify-between items-center">
        <span className="text-xs text-gray-400">
          {new Date(p.created_at).toLocaleDateString()}
        </span>
        <button
          onClick={onClick}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          View →
        </button>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
    </div>
  );
}
