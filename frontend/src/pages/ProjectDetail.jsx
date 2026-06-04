import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  BarChart, Bar, Cell,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { getProject } from '../api/projects';
import { getPanels } from '../api/panels';
import { runOptimisation, getProjectOptimisations, compareOptimisation, getCarbonEstimate } from '../api/optimiser';
import { generateQuote, getProjectQuotes } from '../api/quotes';
import { generateReport, getProjectReports } from '../api/reports';
import Badge from '../components/Badge';
import Spinner from '../components/Spinner';
import ErrorMessage from '../components/ErrorMessage';

const TABS = ['Optimiser', 'Quotes', 'Reports'];
const DISPLAY_WIDTH = 580;

export default function ProjectDetail() {
  const { id } = useParams();
  const projectId = Number(id);

  const [project, setProject] = useState(null);
  const [activeTab, setActiveTab] = useState('Optimiser');
  const [loading, setLoading] = useState(true);

  // Optimiser tab
  const [panels, setPanels] = useState([]);
  const [wallWidth, setWallWidth] = useState(6000);
  const [wallHeight, setWallHeight] = useState(2400);
  const [selectedPanelId, setSelectedPanelId] = useState('');
  const [runLoading, setRunLoading] = useState(false);
  const [runError, setRunError] = useState('');
  const [latestRun, setLatestRun] = useState(null);
  const [pastRuns, setPastRuns] = useState([]);

  // Compare panels
  const [selectedPanelIds, setSelectedPanelIds] = useState([]);
  const [compareWallWidth, setCompareWallWidth] = useState(6000);
  const [compareWallHeight, setCompareWallHeight] = useState(2400);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState('');
  const [compareResult, setCompareResult] = useState(null);

  // Quotes tab
  const [selectedRunId, setSelectedRunId] = useState('');
  const [quoteLoading, setQuoteLoading] = useState(false);
  const [quoteError, setQuoteError] = useState('');
  const [latestQuote, setLatestQuote] = useState(null);
  const [allQuotes, setAllQuotes] = useState([]);

  // Reports tab
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState('');
  const [latestReport, setLatestReport] = useState(null);
  const [allReports, setAllReports] = useState([]);

  useEffect(() => {
    async function init() {
      const [proj, panelList, runs, quotes, reports] = await Promise.all([
        getProject(projectId),
        getPanels(),
        getProjectOptimisations(projectId),
        getProjectQuotes(projectId),
        getProjectReports(projectId),
      ]);
      setProject(proj);
      setPanels(panelList);
      if (panelList.length) setSelectedPanelId(String(panelList[0].id));
      setPastRuns(runs);
      if (runs.length) {
        setLatestRun(runs[0]);
        setSelectedRunId(String(runs[0].id));
      }
      setAllQuotes(quotes);
      if (quotes.length) setLatestQuote(quotes[0]);
      setAllReports(reports);
      if (reports.length) setLatestReport(reports[0]);
      setLoading(false);
    }
    init();
  }, [projectId]);

  async function handleRunOptimisation(e) {
    e.preventDefault();
    setRunError('');
    setRunLoading(true);
    try {
      const run = await runOptimisation({
        project_id: projectId,
        panel_type_id: Number(selectedPanelId),
        wall_width_mm: Number(wallWidth),
        wall_height_mm: Number(wallHeight),
      });
      setLatestRun(run);
      setPastRuns((prev) => [run, ...prev]);
      setSelectedRunId(String(run.id));
    } catch (err) {
      setRunError(err.response?.data?.detail || 'Optimisation failed');
    } finally {
      setRunLoading(false);
    }
  }

  function togglePanelId(id) {
    setSelectedPanelIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }

  async function handleCompare() {
    if (selectedPanelIds.length < 2) {
      setCompareError('Select at least 2 panel types to compare');
      return;
    }
    setCompareError('');
    setCompareLoading(true);
    try {
      const result = await compareOptimisation({
        project_id: projectId,
        wall_width_mm: Number(compareWallWidth),
        wall_height_mm: Number(compareWallHeight),
        panel_type_ids: selectedPanelIds,
      });
      setCompareResult(result);
      setPastRuns((prev) => [...result.runs, ...prev]);
    } catch (err) {
      setCompareError(err.response?.data?.detail || 'Comparison failed');
    } finally {
      setCompareLoading(false);
    }
  }

  async function handleGenerateQuote() {
    if (!selectedRunId) return;
    setQuoteError('');
    setQuoteLoading(true);
    try {
      const quote = await generateQuote(projectId, Number(selectedRunId));
      setLatestQuote(quote);
      setAllQuotes((prev) => [quote, ...prev]);
    } catch (err) {
      setQuoteError(err.response?.data?.detail || 'Quote generation failed');
    } finally {
      setQuoteLoading(false);
    }
  }

  async function handleGenerateReport() {
    setReportError('');
    setReportLoading(true);
    try {
      const report = await generateReport(projectId);
      setLatestReport(report);
      setAllReports((prev) => [report, ...prev]);
    } catch (err) {
      setReportError(err.response?.data?.detail || 'Report generation failed');
    } finally {
      setReportLoading(false);
    }
  }

  if (loading) return <Spinner />;

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
        <Badge status={project.status} />
      </div>
      {project.location && (
        <p className="text-sm text-gray-500 -mt-4 mb-6">{project.location}</p>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-5 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === tab
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Optimiser Tab */}
      {activeTab === 'Optimiser' && (
        <div className="space-y-6">
          <form
            onSubmit={handleRunOptimisation}
            className="bg-white rounded-xl border border-gray-100 shadow-sm p-5"
          >
            <h2 className="font-semibold text-gray-900 mb-4">Run Optimisation</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Wall Width (mm)
                </label>
                <input
                  type="number"
                  value={wallWidth}
                  onChange={(e) => setWallWidth(e.target.value)}
                  min={500}
                  max={50000}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Wall Height (mm)
                </label>
                <input
                  type="number"
                  value={wallHeight}
                  onChange={(e) => setWallHeight(e.target.value)}
                  min={500}
                  max={50000}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Panel Type
                </label>
                <select
                  value={selectedPanelId}
                  onChange={(e) => setSelectedPanelId(e.target.value)}
                  className="input"
                  required
                >
                  {panels.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <ErrorMessage message={runError} onDismiss={() => setRunError('')} />
            <button
              type="submit"
              disabled={runLoading}
              className="mt-4 bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {runLoading && <Spinner size="sm" />}
              {runLoading ? 'Running…' : 'Run Optimisation'}
            </button>
          </form>

          {latestRun && (
            <RunResultCard
              run={latestRun}
              panels={panels}
            />
          )}

          {pastRuns.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100">
                <h3 className="font-semibold text-gray-900">Previous Runs</h3>
              </div>
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
                  <tr>
                    <th className="px-4 py-2 text-left">Date</th>
                    <th className="px-4 py-2 text-left">Wall (W × H)</th>
                    <th className="px-4 py-2 text-right">Waste %</th>
                    <th className="px-4 py-2 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {pastRuns.map((r) => (
                    <tr
                      key={r.id}
                      onClick={() => setLatestRun(r)}
                      className="hover:bg-gray-50 cursor-pointer"
                    >
                      <td className="px-4 py-2 text-gray-600">
                        {new Date(r.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-2 text-gray-600">
                        {r.wall_width_mm} × {r.wall_height_mm} mm
                      </td>
                      <td className="px-4 py-2 text-right">
                        {r.waste_percentage?.toFixed(1) ?? '—'}%
                      </td>
                      <td className="px-4 py-2 text-center">
                        <Badge status={r.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* ── Compare Panels ── */}
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 space-y-4">
            <div>
              <h2 className="font-semibold text-gray-900">Compare Panel Types</h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Run the optimiser across 2–4 panel types on the same wall and compare results.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Wall Width (mm)</label>
                <input
                  type="number"
                  value={compareWallWidth}
                  onChange={(e) => setCompareWallWidth(e.target.value)}
                  min={500}
                  max={50000}
                  className="input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Wall Height (mm)</label>
                <input
                  type="number"
                  value={compareWallHeight}
                  onChange={(e) => setCompareWallHeight(e.target.value)}
                  min={500}
                  max={50000}
                  className="input"
                />
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Panel types to compare (2–4):</p>
              <div className="flex flex-col gap-2">
                {panels.map((panel) => (
                  <label key={panel.id} className="flex items-center gap-2.5 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={selectedPanelIds.includes(panel.id)}
                      onChange={() => togglePanelId(panel.id)}
                      disabled={
                        !selectedPanelIds.includes(panel.id) && selectedPanelIds.length >= 4
                      }
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">
                      {panel.name}
                      <span className="text-gray-400 ml-1">— £{panel.cost_per_unit.toFixed(2)}/panel</span>
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <ErrorMessage message={compareError} onDismiss={() => setCompareError('')} />

            <button
              onClick={handleCompare}
              disabled={compareLoading || selectedPanelIds.length < 2}
              className="bg-indigo-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
            >
              {compareLoading && <Spinner size="sm" />}
              {compareLoading ? 'Comparing…' : 'Compare'}
            </button>

            {compareResult && (
              <CompareResults result={compareResult} panels={panels} />
            )}
          </div>
        </div>
      )}

      {/* Quotes Tab */}
      {activeTab === 'Quotes' && (
        <div className="space-y-5">
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <h2 className="font-semibold text-gray-900 mb-4">Generate Quote</h2>
            {pastRuns.length === 0 ? (
              <p className="text-sm text-gray-500">
                Run an optimisation first before generating a quote.
              </p>
            ) : (
              <div className="flex items-end gap-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Based on optimisation run
                  </label>
                  <select
                    value={selectedRunId}
                    onChange={(e) => setSelectedRunId(e.target.value)}
                    className="input"
                  >
                    {pastRuns.map((r) => (
                      <option key={r.id} value={r.id}>
                        {new Date(r.created_at).toLocaleDateString()} — {r.wall_width_mm}×
                        {r.wall_height_mm}mm — waste {r.waste_percentage?.toFixed(1)}%
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={handleGenerateQuote}
                  disabled={quoteLoading || !selectedRunId}
                  className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {quoteLoading && <Spinner size="sm" />}
                  {quoteLoading ? 'Generating…' : 'Generate Quote'}
                </button>
              </div>
            )}
            <ErrorMessage message={quoteError} onDismiss={() => setQuoteError('')} />
          </div>

          {latestQuote && (
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold text-gray-900">Latest Quote</h3>
                <span className="text-xl font-bold text-green-600">
                  Total: £{latestQuote.total_cost.toLocaleString('en-GB', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 text-sm font-mono whitespace-pre-wrap leading-relaxed text-gray-700 max-h-96 overflow-y-auto">
                {latestQuote.ai_summary}
              </div>
            </div>
          )}

          {allQuotes.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100">
                <h3 className="font-semibold text-gray-900">All Quotes</h3>
              </div>
              <ul className="divide-y divide-gray-50">
                {allQuotes.map((q) => (
                  <li
                    key={q.id}
                    onClick={() => setLatestQuote(q)}
                    className="px-5 py-3 flex justify-between items-center hover:bg-gray-50 cursor-pointer"
                  >
                    <span className="text-sm text-gray-600">
                      {new Date(q.created_at).toLocaleDateString()}
                    </span>
                    <span className="font-semibold text-green-600 text-sm">
                      £{q.total_cost.toLocaleString('en-GB', { minimumFractionDigits: 2 })}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Reports Tab */}
      {activeTab === 'Reports' && (
        <div className="space-y-5">
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="font-semibold text-gray-900">Generate Project Report</h2>
                <p className="text-sm text-gray-500 mt-0.5">
                  AI-generated KTP progress report based on all optimisation runs and quotes.
                </p>
              </div>
              <button
                onClick={handleGenerateReport}
                disabled={reportLoading}
                className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 ml-4 shrink-0"
              >
                {reportLoading && <Spinner size="sm" />}
                {reportLoading ? 'Generating…' : 'Generate Report'}
              </button>
            </div>
            <ErrorMessage message={reportError} onDismiss={() => setReportError('')} />
          </div>

          {latestReport && (
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold text-gray-900">Latest Report</h3>
                <span className="text-xs text-gray-400">
                  {new Date(latestReport.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 text-sm font-mono whitespace-pre-wrap leading-relaxed text-gray-700 max-h-[600px] overflow-y-auto">
                {latestReport.content_markdown}
              </div>
            </div>
          )}

          {allReports.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100">
                <h3 className="font-semibold text-gray-900">All Reports</h3>
              </div>
              <ul className="divide-y divide-gray-50">
                {allReports.map((r) => (
                  <li
                    key={r.id}
                    onClick={() => setLatestReport(r)}
                    className="px-5 py-3 flex justify-between items-center hover:bg-gray-50 cursor-pointer"
                  >
                    <span className="text-sm text-gray-600">
                      Report — {new Date(r.created_at).toLocaleDateString()}
                    </span>
                    <span className="text-xs text-blue-600">View →</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function RunResultCard({ run, panels }) {
  const parsed = run.result_json ? JSON.parse(run.result_json) : null;
  const panelType = panels.find((p) => p.id === run.panel_type_id);

  const chartData = parsed?.fitness_history?.map((fitness, gen) => ({
    gen,
    fitness: parseFloat(fitness.toFixed(2)),
  })) ?? [];

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 space-y-5">
      <h3 className="font-semibold text-gray-900">Optimisation Result</h3>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <MiniStat label="Full Panels" value={parsed?.total_panels ?? '—'} />
        <MiniStat label="Cut Panels" value={parsed?.cut_panels ?? '—'} />
        <MiniStat label="Waste" value={`${(parsed?.waste_percentage ?? 0).toFixed(1)}%`} />
        <MiniStat label="Coverage" value={`${(parsed?.coverage_percentage ?? 0).toFixed(1)}%`} />
      </div>

      {/* Visual panel grid */}
      {parsed && panelType && (
        <PanelGrid
          placements={parsed.placements}
          wallWidth={run.wall_width_mm}
          wallHeight={run.wall_height_mm}
          panelWidth={panelType.width_mm}
          panelHeight={panelType.height_mm}
        />
      )}

      {/* Fitness chart */}
      {chartData.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">
            Fitness over generations
          </p>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="gen"
                tick={{ fontSize: 11 }}
                label={{ value: 'Generation', position: 'insideBottom', offset: -12, fontSize: 11 }}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fontSize: 11 }}
                label={{ value: 'Fitness', angle: -90, position: 'insideLeft', fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{ fontSize: 12 }}
                formatter={(v) => [`${v}`, 'Fitness']}
              />
              <Line
                type="monotone"
                dataKey="fitness"
                stroke="#2563eb"
                strokeWidth={2}
                dot={chartData.length === 1}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <CarbonSection runId={run.id} />
    </div>
  );
}

function PanelGrid({ placements, wallWidth, wallHeight, panelWidth, panelHeight }) {
  const scale = DISPLAY_WIDTH / wallWidth;
  const displayHeight = Math.round(wallHeight * scale);

  return (
    <div>
      <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">
        Panel Layout — {wallWidth} × {wallHeight} mm
      </p>
      <div className="flex justify-center">
        <div
          style={{
            position: 'relative',
            width: DISPLAY_WIDTH,
            height: displayHeight,
            backgroundColor: '#f9fafb',
          }}
          className="border-2 border-gray-400 rounded overflow-hidden"
        >
          {placements.map((panel) => {
            const x1 = Math.max(0, panel.x);
            const y1 = Math.max(0, panel.y);
            const x2 = Math.min(wallWidth, panel.x + panelWidth);
            const y2 = Math.min(wallHeight, panel.y + panelHeight);
            if (x2 <= x1 || y2 <= y1) return null;
            return (
              <div
                key={panel.panel_number}
                style={{
                  position: 'absolute',
                  left: Math.round(x1 * scale),
                  top: Math.round((wallHeight - y2) * scale),
                  width: Math.round((x2 - x1) * scale),
                  height: Math.round((y2 - y1) * scale),
                  backgroundColor: panel.is_full ? '#3b82f6' : '#fb923c',
                  border: '1px solid rgba(255,255,255,0.5)',
                  boxSizing: 'border-box',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 10,
                  color: 'white',
                  fontWeight: 700,
                  overflow: 'hidden',
                }}
              >
                {Math.round((x2 - x1) * scale) > 18 && panel.panel_number}
              </div>
            );
          })}
        </div>
      </div>
      <div className="flex gap-4 mt-2 text-xs text-gray-500 justify-center">
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-blue-500" /> Full panel
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-orange-400" /> Cut panel
        </span>
      </div>
    </div>
  );
}

function MiniStat({ label, value }) {
  return (
    <div className="bg-gray-50 rounded-lg p-3 text-center">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-lg font-bold text-gray-900 mt-0.5">{value}</p>
    </div>
  );
}

function CarbonSection({ runId }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);

  useEffect(() => {
    setData(null);
    setError('');
  }, [runId]);

  async function handleCalculate() {
    setError('');
    setLoading(true);
    try {
      setData(await getCarbonEstimate(runId));
    } catch (err) {
      setError(err.response?.data?.detail || 'Carbon estimate failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="border-t border-gray-100 pt-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Carbon Footprint</p>
        <button
          onClick={handleCalculate}
          disabled={loading}
          className="flex items-center gap-1.5 bg-emerald-600 text-white text-xs px-3 py-1.5 rounded-lg hover:bg-emerald-700 disabled:opacity-50"
        >
          {loading && <Spinner size="sm" />}
          {loading ? 'Calculating…' : 'Calculate Carbon Impact'}
        </button>
      </div>
      <ErrorMessage message={error} onDismiss={() => setError('')} />
      {data && <CarbonCards data={data} />}
    </div>
  );
}

function CarbonCards({ data }) {
  const { sip_carbon: sip, traditional_carbon: trad, saving } = data;

  const barData = [
    { name: 'SIP Construction', carbon: sip.total_kgco2e, fill: '#3b82f6' },
    { name: 'Traditional Build', carbon: trad.total_kgco2e, fill: '#9ca3af' },
  ];

  const savingColour = saving.is_lower_carbon
    ? { bg: 'bg-green-50', border: 'border-green-200', title: 'text-green-600', val: 'text-green-900', detail: 'text-green-700' }
    : { bg: 'bg-red-50', border: 'border-red-200', title: 'text-red-600', val: 'text-red-900', detail: 'text-red-700' };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
        {/* SIP card */}
        <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
          <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-1">
            SIP Construction
          </p>
          <p className="text-2xl font-bold text-blue-900">
            {sip.total_kgco2e.toFixed(1)}
            <span className="text-xs font-normal ml-1">kgCO₂e</span>
          </p>
          <div className="mt-2 text-xs text-blue-700 space-y-0.5">
            <p>Embodied: {sip.embodied_kgco2e.toFixed(1)} kgCO₂e</p>
            <p>Transport: {sip.transport_kgco2e.toFixed(1)} kgCO₂e</p>
            <p>Per panel: {sip.carbon_per_panel.toFixed(2)} kgCO₂e</p>
          </div>
        </div>

        {/* Traditional card */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
            Traditional Build
          </p>
          <p className="text-2xl font-bold text-gray-800">
            {trad.total_kgco2e.toFixed(1)}
            <span className="text-xs font-normal ml-1">kgCO₂e</span>
          </p>
          <div className="mt-2 text-xs text-gray-600 space-y-0.5">
            <p>Wall area: {trad.wall_area_m2.toFixed(2)} m²</p>
            <p>Rate: {trad.carbon_per_m2} kgCO₂e/m²</p>
          </div>
        </div>

        {/* Saving card */}
        <div className={`${savingColour.bg} ${savingColour.border} border rounded-lg p-3`}>
          <p className={`text-xs font-semibold uppercase tracking-wide mb-1 ${savingColour.title}`}>
            Carbon Saving
          </p>
          <p className={`text-2xl font-bold ${savingColour.val}`}>
            {Math.abs(saving.saving_kgco2e).toFixed(1)}
            <span className="text-xs font-normal ml-1">kgCO₂e</span>
          </p>
          <div className={`mt-2 text-xs space-y-0.5 ${savingColour.detail}`}>
            <p>
              {Math.abs(saving.saving_percentage).toFixed(1)}%{' '}
              {saving.is_lower_carbon ? 'reduction' : 'increase'} vs traditional
            </p>
            <p>≈ {saving.trees_equivalent.toFixed(1)} trees/year equivalent</p>
          </div>
        </div>
      </div>

      {/* Comparison bar chart */}
      <div>
        <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">
          Carbon comparison — SIP vs Traditional (kgCO₂e)
        </p>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={barData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 11 }} unit=" kg" />
            <Tooltip
              contentStyle={{ fontSize: 12 }}
              formatter={(v) => [`${v.toFixed(1)} kgCO₂e`, 'Carbon']}
            />
            <Bar dataKey="carbon" radius={[3, 3, 0, 0]}>
              {barData.map((entry, i) => (
                <Cell key={i} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function CompareResults({ result, panels }) {
  const chartData = result.runs.map((run) => {
    const panel = panels.find((p) => p.id === run.panel_type_id);
    const shortName = panel?.name?.split(' ').slice(0, 3).join(' ') ?? `Panel ${run.panel_type_id}`;
    return {
      name: shortName,
      waste: run.waste_percentage ?? 0,
      isWinner: run.panel_type_id === result.best_panel_type_id,
    };
  });

  return (
    <div className="space-y-4 pt-2 border-t border-gray-100">
      {/* Summary banner */}
      <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-2.5 text-sm text-green-800 font-medium">
        {result.summary}
      </div>

      {/* Comparison table */}
      <div className="overflow-x-auto rounded-lg border border-gray-100">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th className="px-3 py-2 text-left">Panel Type</th>
              <th className="px-3 py-2 text-right">Full Panels</th>
              <th className="px-3 py-2 text-right">Cut Panels</th>
              <th className="px-3 py-2 text-right">Waste %</th>
              <th className="px-3 py-2 text-right">Cost/Panel</th>
              <th className="px-3 py-2 text-center w-16"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {result.runs.map((run) => {
              const panel = panels.find((p) => p.id === run.panel_type_id);
              const parsed = run.result_json ? JSON.parse(run.result_json) : {};
              const isWinner = run.panel_type_id === result.best_panel_type_id;
              return (
                <tr key={run.id} className={isWinner ? 'bg-green-50' : 'bg-white'}>
                  <td className="px-3 py-2 font-medium text-gray-900">{panel?.name ?? '—'}</td>
                  <td className="px-3 py-2 text-right text-gray-600">{parsed.total_panels ?? '—'}</td>
                  <td className="px-3 py-2 text-right text-gray-600">{parsed.cut_panels ?? '—'}</td>
                  <td className="px-3 py-2 text-right text-gray-600">
                    {run.waste_percentage?.toFixed(1) ?? '—'}%
                  </td>
                  <td className="px-3 py-2 text-right text-gray-600">
                    £{panel?.cost_per_unit?.toFixed(2) ?? '—'}
                  </td>
                  <td className="px-3 py-2 text-center">
                    {isWinner && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                        Best
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Waste % bar chart */}
      <div>
        <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">
          Waste comparison
        </p>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 45 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11 }}
              angle={-20}
              textAnchor="end"
              interval={0}
            />
            <YAxis
              tick={{ fontSize: 11 }}
              unit="%"
              allowDecimals={false}
            />
            <Tooltip formatter={(v) => [`${v}%`, 'Waste']} contentStyle={{ fontSize: 12 }} />
            <Bar dataKey="waste" radius={[3, 3, 0, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.isWinner ? '#22c55e' : '#3b82f6'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
