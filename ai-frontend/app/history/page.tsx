"use client";
import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import AdCard from "../components/AdCard";
import SearchBar from "../components/SearchBar";
import { API_URL } from "../../lib/api";

type Ad = {
  id: string;
  product: string;
  hook: string;
  angle: string;
  positioning: string;
  copy: string;
  creative: string;
  qa_score: string;
  media: string;
  images: string | null;
  voiceover_url: string | null;
  compliance_status: string | null;
  tiktok_caption: string | null;
  video_url: string | null;
  created_at: string;
};

export default function HistoryPage() {
  const [ads, setAds] = useState<Ad[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchAds = useCallback(async (search = "") => {
    try {
      setLoading(true);
      const params = search ? `?search=${encodeURIComponent(search)}` : "";
      const res = await axios.get(`${API_URL}/ads${params}`);
      setAds(res.data);
    } catch {
      setError("Failed to load ads. Is your backend running?");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAds();
  }, [fetchAds]);

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Ad History</h1>
        <p className="text-gray-400">All your previously generated ads</p>
      </div>

      <div className="mb-6">
        <SearchBar onSearch={fetchAds} />
      </div>

      {loading && (
        <p className="text-gray-400 text-center py-12">Loading ads...</p>
      )}

      {error && (
        <p className="text-red-400 text-center py-12">{error}</p>
      )}

      {!loading && !error && ads.length === 0 && (
        <p className="text-gray-500 text-center py-12">
          No ads found. Generate your first ad!
        </p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {ads.map((ad) => (
          <AdCard key={ad.id} ad={ad} />
        ))}
      </div>
    </div>
  );
}
