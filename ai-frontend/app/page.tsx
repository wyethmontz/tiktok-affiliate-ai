"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { API_URL } from "../lib/api";

export default function Home() {
  const [product, setProduct] = useState("");

  const [imageUrls, setImageUrls] = useState<string[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [videoUrls, setVideoUrls] = useState<string[]>([]);
  const [videoNames, setVideoNames] = useState<string[]>([]);
  const [showImageInputs, setShowImageInputs] = useState(false);
  const [showVideoInputs, setShowVideoInputs] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadingVideo, setUploadingVideo] = useState(false);
  const [pasteUrl, setPasteUrl] = useState("");
  const [result, setResult] = useState<Record<string, string> | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState("");
  const [error, setError] = useState("");
  const [captionCopied, setCaptionCopied] = useState(false);
  const [usedProductImages, setUsedProductImages] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [dragOverVideo, setDragOverVideo] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("reuse_ad");
    if (saved) {
      const data = JSON.parse(saved);
      setProduct(data.product || "");
      localStorage.removeItem("reuse_ad");
    }
  }, []);

  async function uploadFiles(files: FileList | File[]) {
    const fileArray = Array.from(files).filter(f => f.type.startsWith("image/"));
    if (fileArray.length === 0) return;

    const remaining = 4 - imageUrls.length;
    const toUpload = fileArray.slice(0, remaining);
    if (toUpload.length === 0) return;

    setUploading(true);
    for (const file of toUpload) {
      try {
        const formData = new FormData();
        formData.append("file", file);
        const res = await axios.post(`${API_URL}/upload-image`, formData);
        setImageUrls(prev => [...prev, res.data.url]);
        setImagePreviews(prev => [...prev, URL.createObjectURL(file)]);
      } catch {
        setError("Failed to upload image");
      }
    }
    setUploading(false);
  }

  function removeImage(index: number) {
    setImageUrls(prev => prev.filter((_, i) => i !== index));
    setImagePreviews(prev => prev.filter((_, i) => i !== index));
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length > 0) {
      uploadFiles(e.dataTransfer.files);
    }
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files.length > 0) {
      uploadFiles(e.target.files);
      e.target.value = "";
    }
  }

  function convertImageUrl(url: string): string {
    // Google Drive share link → direct download
    const driveMatch = url.match(/drive\.google\.com\/file\/d\/([^/]+)/);
    if (driveMatch) {
      return `https://drive.google.com/uc?export=download&id=${driveMatch[1]}`;
    }
    return url;
  }

  function getPreviewUrl(url: string): string {
    // Google Drive → thumbnail for preview
    const driveMatch = url.match(/drive\.google\.com\/file\/d\/([^/]+)/);
    if (driveMatch) {
      return `https://drive.google.com/thumbnail?id=${driveMatch[1]}&sz=w400`;
    }
    return url;
  }

  function addImageUrl() {
    const url = pasteUrl.trim();
    if (!url || imageUrls.length >= 4) return;

    const directUrl = convertImageUrl(url);
    const previewUrl = getPreviewUrl(url);

    setImageUrls(prev => [...prev, directUrl]);
    setImagePreviews(prev => [...prev, previewUrl]);
    setPasteUrl("");
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

  async function uploadVideoFiles(files: FileList | File[]) {
    const fileArray = Array.from(files).filter(f => f.type.startsWith("video/"));
    if (fileArray.length === 0) return;

    const remaining = 5 - videoUrls.length;
    const toUpload = fileArray.slice(0, remaining);
    if (toUpload.length === 0) return;

    setUploadingVideo(true);
    for (const file of toUpload) {
      try {
        const formData = new FormData();
        formData.append("file", file);
        const res = await axios.post(`${API_URL}/upload-video`, formData);
        setVideoUrls(prev => [...prev, res.data.url]);
        setVideoNames(prev => [...prev, file.name]);
      } catch {
        setError("Failed to upload video");
      }
    }
    setUploadingVideo(false);
  }

  function removeVideo(index: number) {
    setVideoUrls(prev => prev.filter((_, i) => i !== index));
    setVideoNames(prev => prev.filter((_, i) => i !== index));
  }

  function handleVideoDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOverVideo(false);
    if (e.dataTransfer.files.length > 0) {
      uploadVideoFiles(e.dataTransfer.files);
    }
  }

  function handleVideoInput(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files.length > 0) {
      uploadVideoFiles(e.target.files);
      e.target.value = "";
    }
  }

  async function generateAd() {
    setLoading(true);
    setError("");
    setResult(null);
    setCaptionCopied(false);
    setCurrentStep("Starting pipeline...");

    const filteredUrls = imageUrls.filter(url => url.trim() !== "");
    setUsedProductImages(filteredUrls.length > 0 || videoUrls.length > 0);
    setShowImageInputs(false);
    setShowVideoInputs(false);

    try {
      const res = await axios.post(`${API_URL}/generate-ad`, {
        product: product,
        product_image_urls: filteredUrls,
        user_video_urls: videoUrls,
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
      <p className="text-gray-400 mb-8">Drop your product + images, AI handles the rest</p>

      <div className="flex flex-col gap-4 mb-6">
        <input
          placeholder="What are you promoting? (e.g. Cute LED Night Light, Lip Tint Set)"
          value={product}
          onChange={(e) => setProduct(e.target.value)}
          className="bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:border-pink-500"
        />

        {/* Product Images — Drag & Drop */}
        <div>
          <button
            type="button"
            onClick={() => setShowImageInputs(!showImageInputs)}
            className="text-sm text-pink-400 hover:text-pink-300 transition-colors"
          >
            {showImageInputs ? "- Hide product images" : `+ Add product images${imageUrls.length > 0 ? ` (${imageUrls.length})` : " (optional)"}`}
          </button>

          {showImageInputs && (
            <div className="mt-3 flex flex-col gap-3">
              <p className="text-xs text-gray-500">
                Drop photos, browse files, or paste a Google Drive / image link.
              </p>

              {/* URL paste input */}
              {imageUrls.length < 4 && (
                <div className="flex gap-2">
                  <input
                    placeholder="Paste image URL or Google Drive link"
                    value={pasteUrl}
                    onChange={(e) => setPasteUrl(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && addImageUrl()}
                    className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-pink-500"
                  />
                  <button
                    type="button"
                    onClick={addImageUrl}
                    disabled={!pasteUrl.trim()}
                    className="bg-pink-600 hover:bg-pink-500 disabled:bg-gray-700 text-white text-sm px-4 rounded-lg transition-colors"
                  >
                    Add
                  </button>
                </div>
              )}

              {/* Drop zone */}
              {imageUrls.length < 4 && (
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                  onClick={() => document.getElementById("file-input")?.click()}
                  className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${
                    dragOver
                      ? "border-pink-500 bg-pink-500/10"
                      : "border-gray-600 hover:border-gray-500 bg-gray-800/50"
                  }`}
                >
                  <input
                    id="file-input"
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={handleFileInput}
                    className="hidden"
                  />
                  {uploading ? (
                    <p className="text-pink-400 text-sm">Uploading...</p>
                  ) : (
                    <p className="text-gray-400 text-sm">
                      Drag & drop images here or click to browse
                    </p>
                  )}
                </div>
              )}

              {/* Image previews */}
              {imagePreviews.length > 0 && (
                <div className="grid grid-cols-4 gap-2">
                  {imagePreviews.map((preview, i) => (
                    <div key={i} className="relative group">
                      <img
                        src={preview}
                        alt={`Product ${i + 1}`}
                        className="w-full aspect-square object-cover rounded-lg border border-gray-700"
                      />
                      <button
                        type="button"
                        onClick={() => removeImage(i)}
                        className="absolute top-1 right-1 bg-black/70 text-white rounded-full w-5 h-5 text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        x
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Video Clips — Drag & Drop */}
        <div>
          <button
            type="button"
            onClick={() => setShowVideoInputs(!showVideoInputs)}
            className="text-sm text-purple-400 hover:text-purple-300 transition-colors"
          >
            {showVideoInputs ? "- Hide video clips" : `+ Add your video clips${videoUrls.length > 0 ? ` (${videoUrls.length})` : " (recommended for sales)"}`}
          </button>

          {showVideoInputs && (
            <div className="mt-3 flex flex-col gap-3">
              <p className="text-xs text-gray-500">
                Record 5-10 sec clips on your phone — hands holding product, unboxing, using it. AI adds script, voiceover, captions.
              </p>

              {/* Drop zone */}
              {videoUrls.length < 5 && (
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragOverVideo(true); }}
                  onDragLeave={() => setDragOverVideo(false)}
                  onDrop={handleVideoDrop}
                  onClick={() => document.getElementById("video-input")?.click()}
                  className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${
                    dragOverVideo
                      ? "border-purple-500 bg-purple-500/10"
                      : "border-gray-600 hover:border-gray-500 bg-gray-800/50"
                  }`}
                >
                  <input
                    id="video-input"
                    type="file"
                    accept="video/*"
                    multiple
                    onChange={handleVideoInput}
                    className="hidden"
                  />
                  {uploadingVideo ? (
                    <p className="text-purple-400 text-sm">Uploading video...</p>
                  ) : (
                    <p className="text-gray-400 text-sm">
                      Drag & drop video clips here or click to browse (max 5, 50MB each)
                    </p>
                  )}
                </div>
              )}

              {/* Video list */}
              {videoNames.length > 0 && (
                <div className="flex flex-col gap-1">
                  {videoNames.map((name, i) => (
                    <div key={i} className="flex items-center justify-between bg-gray-800 rounded-lg px-3 py-2 text-sm">
                      <span className="text-gray-300 truncate">{name}</span>
                      <button
                        type="button"
                        onClick={() => removeVideo(i)}
                        className="text-gray-500 hover:text-red-400 ml-2"
                      >
                        x
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <button
          onClick={generateAd}
          disabled={loading || !product.trim()}
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

            {/* TikTok Video */}
            {result.video_url && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-semibold text-gray-400">TikTok Video</h3>
                  <a
                    href={result.video_url}
                    download="tiktok-ad.mp4"
                    className="text-xs bg-pink-600 hover:bg-pink-500 text-white px-3 py-1 rounded-lg transition-colors"
                  >
                    Download MP4
                  </a>
                </div>
                <video
                  controls
                  className="w-full max-w-sm mx-auto rounded-lg border border-gray-700"
                  style={{ aspectRatio: "9/16" }}
                >
                  <source src={result.video_url} type="video/mp4" />
                </video>
              </div>
            )}

            {result.voiceover_url && !result.video_url && (
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
