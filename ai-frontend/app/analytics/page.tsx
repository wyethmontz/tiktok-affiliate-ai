"use client";
import { useEffect, useState } from "react";
import axios from "axios";
import { API_URL } from "../../lib/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

type Summary = {
  total_ads: number;
  avg_score: number;
  top_hooks: { hook: string; product: string; score: number }[];
  ads_by_platform: Record<string, number>;
  score_distribution: { low: number; mid: number; high: number; excellent: number };
};

const SCORE_COLORS = ["#ef4444", "#f59e0b", "#3b82f6", "#22c55e"];

export default function AnalyticsPage() {
  const [data, setData] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [insights, setInsights] = useState("");
  const [insightsLoading, setInsightsLoading] = useState(false);

  useEffect(() => {
    axios
      .get(`${API_URL}/analytics/summary`)
      .then((res) => setData(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="text-gray-400 text-center py-12">Loading analytics...</p>;
  }

  if (!data || data.total_ads === 0) {
    return (
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Analytics</h1>
        <p className="text-gray-500 text-center py-12">
          No data yet. Generate some ads first!
        </p>
      </div>
    );
  }

  const scoreData = [
    { name: "1-3", value: data.score_distribution.low, fill: SCORE_COLORS[0] },
    { name: "4-6", value: data.score_distribution.mid, fill: SCORE_COLORS[1] },
    { name: "7-8", value: data.score_distribution.high, fill: SCORE_COLORS[2] },
    { name: "9-10", value: data.score_distribution.excellent, fill: SCORE_COLORS[3] },
  ];

  const platformData = Object.entries(data.ads_by_platform).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Analytics</h1>
        <p className="text-gray-400">Performance insights across all generated ads</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
          <p className="text-sm text-gray-400">Total Ads</p>
          <p className="text-3xl font-bold text-white">{data.total_ads}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
          <p className="text-sm text-gray-400">Avg QA Score</p>
          <p className="text-3xl font-bold text-blue-400">{data.avg_score}/10</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
          <p className="text-sm text-gray-400">Top Score</p>
          <p className="text-3xl font-bold text-green-400">
            {data.top_hooks.length > 0 ? `${data.top_hooks[0].score}/10` : "N/A"}
          </p>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Score distribution */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-400 mb-4">Score Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={scoreData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" allowDecimals={false} />
              <Tooltip
                contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151" }}
                labelStyle={{ color: "#9ca3af" }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {scoreData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Platform breakdown */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-400 mb-4">Ads by Platform</h3>
          {platformData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={platformData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="55%"
                  outerRadius={80}
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {platformData.map((_, i) => (
                    <Cell
                      key={i}
                      fill={["#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b", "#22c55e"][i % 5]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151" }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No platform data</p>
          )}
        </div>
      </div>

      {/* AI Insights */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 mb-8">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-semibold text-gray-400">AI Insights</h3>
          <button
            onClick={async () => {
              setInsightsLoading(true);
              try {
                const res = await axios.get(`${API_URL}/analytics/insights`);
                setInsights(res.data.insights);
              } catch {
                setInsights("Failed to load insights.");
              }
              setInsightsLoading(false);
            }}
            disabled={insightsLoading}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 text-white text-xs font-semibold px-3 py-1 rounded-lg transition-colors"
          >
            {insightsLoading ? "Analyzing..." : "Generate Insights"}
          </button>
        </div>
        {insights ? (
          <p className="text-gray-200 text-sm whitespace-pre-wrap">{insights}</p>
        ) : (
          <p className="text-gray-500 text-sm">
            Click &quot;Generate Insights&quot; to analyze your top-performing ads with AI.
          </p>
        )}
      </div>

      {/* Top hooks table */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-gray-400 mb-4">Top Performing Hooks</h3>
        <table className="w-full text-left">
          <thead>
            <tr className="text-gray-400 text-sm border-b border-gray-700">
              <th className="pb-2">Hook</th>
              <th className="pb-2">Product</th>
              <th className="pb-2 text-right">Score</th>
            </tr>
          </thead>
          <tbody>
            {data.top_hooks.map((item, i) => (
              <tr key={i} className="border-b border-gray-700/50">
                <td className="py-2 text-white text-sm">{item.hook}</td>
                <td className="py-2 text-gray-300 text-sm">{item.product}</td>
                <td className="py-2 text-right">
                  <span className="bg-blue-600 text-white text-xs font-bold px-2 py-1 rounded-full">
                    {item.score}/10
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
