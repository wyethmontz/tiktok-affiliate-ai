"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { API_URL } from "../lib/api";

export default function Home() {
  const [form, setForm] = useState({
    product: "",
    audience: "",
    goal: "",
    affiliate_link: "",
  });

  const [imageUrls, setImageUrls] = useState<string[]>([""]);
  const [showImageInputs, setShowImageInputs] = useState(false);
  const [result, setResult] = useState<Record<string, string> | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState("");
  const [error, setError] = useState("");
  const [captionCopied, setCaptionCopied] = useState(false);
  const [usedProductImages, setUsedProductImages] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("reuse_ad");
    if (saved) {
      const data = JSON.parse(saved);
      setForm((prev) => ({
        ...prev,
        product: data.product || "",
      }));
      localStorage.removeItem("reuse_ad");
    }
  }, []);

  function updateField(e: React.ChangeEvent<HTMLInputElement>) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  function updateImageUrl(index: number, value: string) {
    const updated = [...imageUrls];
    updated[index] = value;
    setImageUrls(updated);
  }

  function addImageUrl() {
    if (imageUrls.length < 4) {
      setImageUrls([...imageUrls, ""]);
    }
  }

  function removeImageUrl(index: number) {
    const updated = imageUrls.filter((_, i) => i !== index);
    setImageUrls(updated.length === 0 ? [""] : updated);
  }

  async function pollJob(jobId: string) {
    const poll = async (): Promise<void> => {
      const res = await axios.get(`${API_URL}/jobs/${jobId}`);
      const job = res.data;

      if (job.current_step) {
        setCurrentStep(job.current_step);
      }

      if (job.status === "completed") {
        setResult(job.result);
        setLoading(false);
        setCurrentStep("");
      } else if (job.status === "failed") {
        setError(job.error || "Ad generation failed");
        setLoading(false);
        setCurrentStep("");
      } else {
        await new Promise((r) => setTimeout(r, 2000));
        return poll();
      }
    };
    await poll();
  }

  async function generateAd() {
    setLoading(true);
    setError("");
    setResult(null);
    setCaptionCopied(false);
    setCurrentStep("Starting pipeline...");

    const filteredUrls = imageUrls.filter(url => url.trim() !== "");
    setUsedProductImages(filteredUrls.length > 0);

    try {
      const res = await axios.post(`${API_URL}/generate-ad`, {
        ...form,
        product_image_urls: filteredUrls,
      });
      await pollJob(res.data.job_id);
    } catch {
      setError("Failed to connect to backend. Is it running?");
      setLoading(false);
      setCurrentStep("");
    }
  }

  function copyCaption() {
    if (result?.tiktok_caption) {
      navigator.clipboard.writeText(result.tiktok_caption);
      setCaptionCopied(true);
      setTimeout(() => setCaptionCopied(false), 2000);
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">TikTok Ad Generator</h1>
      <p className="text-gray-400 mb-8">Create TikTok-compliant affiliate content with AI</p>

      <div className="flex flex-col gap-4 mb-6">
        <input
          name="product"
          placeholder="Product (e.g. Lip Tint, LED Mirror)"
          value={form.product}
          onChange={updateField}
          className="bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-pink-500"
        />
        <input
          name="audience"
          placeholder="Audience (e.g. Gen Z women in school)"
          value={form.audience}
          onChange={updateField}
          className="bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-pink-500"
        />
        <input
          name="goal"
          placeholder="Goal (e.g. Drive affiliate sales)"
          value={form.goal}
          onChange={updateField}
          className="bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-pink-500"
        />
        <input
          name="affiliate_link"
          placeholder="Affiliate link (optional)"
          value={form.affiliate_link}
          onChange={updateField}
          className="bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-pink-500"
        />

        {/* Product Image URLs */}
        <div>
          <button
            type="button"
            onClick={() => setShowImageInputs(!showImageInputs)}
            className="text-sm text-pink-400 hover:text-pink-300 transition-colors"
          >
            {showImageInputs ? "- Hide product images" : "+ Add product images (optional)"}
          </button>

          {showImageInputs && (
            <div className="mt-3 flex flex-col gap-2">
              <p className="text-xs text-gray-500">Paste image URLs from Shopee, Lazada, or TikTok Shop. Skips AI image generation.</p>
              {imageUrls.map((url, i) => (
                <div key={i} className="flex gap-2">
                  <input
                    placeholder="https://... (product image URL)"
                    value={url}
                    onChange={(e) => updateImageUrl(i, e.target.value)}
                    className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-pink-500"
                  />
                  <button
                    type="button"
                    onClick={() => removeImageUrl(i)}
                    className="text-gray-500 hover:text-red-400 px-2"
                  >
                    x
                  </button>
                </div>
              ))}
              {imageUrls.length < 4 && (
                <button
                  type="button"
                  onClick={addImageUrl}
                  className="text-xs text-gray-400 hover:text-pink-400 text-left"
                >
                  + Add another image (max 4)
                </button>
              )}
            </div>
          )}
        </div>

        <button
          onClick={generateAd}
          disabled={loading}
          className="bg-pink-600 hover:bg-pink-500 disabled:bg-gray-600 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
        >
          {loading ? "Generating..." : "Generate TikTok Ad"}
        </button>
      </div>

      {loading && currentStep && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 border-2 border-pink-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-pink-400 font-medium">{currentStep}</p>
          </div>
        </div>
      )}

      {error && (
        <p className="text-red-400 text-center py-4">{error}</p>
      )}

      {result && (
        <div className="flex flex-col gap-4">
          {/* AIGC Disclosure Banner */}
          <div className="bg-yellow-900/30 border border-yellow-600/50 rounded-xl p-4">
            <p className="text-yellow-400 font-semibold text-sm mb-2">AI-Generated Content Notice</p>
            <p className="text-yellow-200/80 text-xs">
              This content was created with AI. When posting to TikTok, you must enable the AIGC label:
            </p>
            <ol className="text-yellow-200/80 text-xs mt-1 ml-4 list-decimal">
              <li>Tap More options (...) on the post screen</li>
              <li>Turn on &quot;AI-generated content&quot; setting</li>
            </ol>
            <p className="text-yellow-200/60 text-xs mt-1">Labeling does not affect your video distribution.</p>
          </div>

          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold">Result</h2>
              {result.compliance_status && (
                <span className={`text-sm font-bold px-3 py-1 rounded-full ${
                  result.compliance_status === "PASS"
                    ? "bg-green-600 text-white"
                    : "bg-red-600 text-white"
                }`}>
                  {result.compliance_status === "PASS" ? "TikTok Compliant" : "Compliance Issues"}
                </span>
              )}
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-400 mb-1">Hook</h3>
              <p className="text-white">{result.hook}</p>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-400 mb-1">Angle</h3>
              <p className="text-white">{result.angle}</p>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-400 mb-1">Positioning</h3>
              <p className="text-white">{result.positioning}</p>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-400 mb-1">TikTok Script</h3>
              <p className="text-white whitespace-pre-wrap">{result.copy}</p>
            </div>

            {/* TikTok Caption — Copy-Paste Ready */}
            {result.tiktok_caption && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-sm font-semibold text-gray-400">TikTok Caption</h3>
                  <button
                    onClick={copyCaption}
                    className="text-xs bg-pink-600 hover:bg-pink-500 text-white px-3 py-1 rounded-lg transition-colors"
                  >
                    {captionCopied ? "Copied!" : "Copy Caption"}
                  </button>
                </div>
                <div className="bg-gray-900 border border-gray-600 rounded-lg p-3">
                  <p className="text-white whitespace-pre-wrap text-sm">{result.tiktok_caption}</p>
                </div>
              </div>
            )}

            <div>
              <h3 className="text-sm font-semibold text-gray-400 mb-1">Scene Plan</h3>
              <p className="text-white whitespace-pre-wrap">{result.creative}</p>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-400 mb-1">QA Score</h3>
              <p className="text-white whitespace-pre-wrap">{result.qa_score}</p>
            </div>

            {result.voiceover_url && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Voiceover</h3>
                <audio controls className="w-full">
                  <source src={result.voiceover_url} type="audio/mpeg" />
                </audio>
              </div>
            )}

            {result.images && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">
                  {usedProductImages ? "Product Images" : "Generated Images (9:16 TikTok)"}
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {result.images.split(",").map((url: string, i: number) => (
                    <img
                      key={i}
                      src={url}
                      alt={`Scene ${i + 1}`}
                      className="rounded-lg w-full object-cover border border-gray-700"
                    />
                  ))}
                </div>
              </div>
            )}

            <div>
              <h3 className="text-sm font-semibold text-gray-400 mb-1">Image Prompts</h3>
              <p className="text-white whitespace-pre-wrap text-sm">{result.media}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
