"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
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

export default function AdCard({ ad }: { ad: Ad }) {
  const router = useRouter();
  const [expanded, setExpanded] = useState(false);
  const [fullAd, setFullAd] = useState<Ad | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [captionCopied, setCaptionCopied] = useState(false);

  const scoreMatch = ad.qa_score?.match(/\d+/);
  const score = scoreMatch ? scoreMatch[0] : "?";
  const isDiscovery = ad.compliance_status === "DISCOVERY";

  const handleReuse = () => {
    localStorage.setItem(
      "reuse_ad",
      JSON.stringify({
        product: ad.product,
        hook: ad.hook,
        angle: ad.angle,
      })
    );
    router.push("/");
  };

  const copyCaption = () => {
    if (ad.tiktok_caption) {
      navigator.clipboard.writeText(ad.tiktok_caption);
      setCaptionCopied(true);
      setTimeout(() => setCaptionCopied(false), 2000);
    }
  };

  const firstImage = ad.images ? ad.images.split(",")[0] : null;

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 flex flex-col gap-3">
      {firstImage && (
        <div className="relative">
          <img
            src={firstImage}
            alt={ad.product}
            className="rounded-lg w-full h-48 object-cover border border-gray-700"
          />
          <span className="absolute top-2 left-2 bg-black/70 text-yellow-400 text-xs font-semibold px-2 py-0.5 rounded">
            AI Generated
          </span>
          {ad.video_url && (
            <span className="absolute top-2 right-2 bg-pink-600 text-white text-xs font-semibold px-2 py-0.5 rounded">
              Video
            </span>
          )}
        </div>
      )}
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-lg font-bold text-white">{ad.product}</h3>
          <p className="text-sm text-gray-400">
            {new Date(ad.created_at).toLocaleDateString()}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          {!isDiscovery && (
            <span className="bg-pink-600 text-white text-sm font-bold px-3 py-1 rounded-full">
              {score}/10
            </span>
          )}
          {ad.compliance_status && (
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
              ad.compliance_status === "PASS"
                ? "bg-green-600/20 text-green-400"
                : isDiscovery
                  ? "bg-purple-600/20 text-purple-300"
                  : "bg-red-600/20 text-red-400"
            }`}>
              {ad.compliance_status === "PASS"
                ? "Compliant"
                : isDiscovery
                  ? "Discovery"
                  : "Issues"}
            </span>
          )}
        </div>
      </div>

      <p className="text-gray-200 text-sm italic">&quot;{ad.hook}&quot;</p>

      <div className="flex gap-2 flex-wrap">
        <span className="bg-gray-700 text-gray-300 text-xs px-2 py-1 rounded">
          TikTok
        </span>
        <span className="bg-gray-700 text-gray-300 text-xs px-2 py-1 rounded">
          {ad.angle}
        </span>
      </div>

      {/* Expand/Collapse toggle */}
      <button
        onClick={async () => {
          if (!expanded && !fullAd) {
            setLoadingDetails(true);
            try {
              const res = await axios.get(`${API_URL}/ads/${ad.id}`);
              setFullAd(res.data);
            } catch {
              // Use what we have
            }
            setLoadingDetails(false);
          }
          setExpanded(!expanded);
        }}
        className="text-sm text-pink-400 hover:text-pink-300 transition-colors text-left"
      >
        {loadingDetails ? "Loading..." : expanded ? "- Hide details" : "+ Show full details"}
      </button>

      {/* Expanded details */}
      {expanded && (
        <div className="flex flex-col gap-4 border-t border-gray-700 pt-4">
          {/* Video */}
          {(fullAd?.video_url || ad.video_url) && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold text-gray-400">TikTok Video</h4>
                <a
                  href={fullAd?.video_url ?? ad.video_url ?? undefined}
                  download="tiktok-ad.mp4"
                  className="text-xs bg-pink-600 hover:bg-pink-500 text-white px-3 py-1 rounded-lg transition-colors"
                >
                  Download MP4
                </a>
              </div>
              <video
                controls
                className="w-full rounded-lg border border-gray-700"
                style={{ aspectRatio: "9/16", maxHeight: "400px" }}
              >
                <source src={fullAd?.video_url ?? ad.video_url ?? ""} type="video/mp4" />
              </video>
            </div>
          )}

          {/* TikTok Caption */}
          {ad.tiktok_caption && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <h4 className="text-sm font-semibold text-gray-400">TikTok Caption</h4>
                <button
                  onClick={copyCaption}
                  className="text-xs bg-pink-600 hover:bg-pink-500 text-white px-3 py-1 rounded-lg transition-colors"
                >
                  {captionCopied ? "Copied!" : "Copy"}
                </button>
              </div>
              <div className="bg-gray-900 border border-gray-600 rounded-lg p-3">
                <p className="text-white whitespace-pre-wrap text-sm">{ad.tiktok_caption}</p>
              </div>
            </div>
          )}

          {/* Script — affiliate only (discovery has no script) */}
          {!isDiscovery && ad.copy && (
            <div>
              <h4 className="text-sm font-semibold text-gray-400 mb-1">Script</h4>
              <p className="text-white whitespace-pre-wrap text-sm">{ad.copy}</p>
            </div>
          )}

          {/* Positioning */}
          {ad.positioning && (
            <div>
              <h4 className="text-sm font-semibold text-gray-400 mb-1">Positioning</h4>
              <p className="text-white text-sm">{ad.positioning}</p>
            </div>
          )}

          {/* Scene Plan — affiliate only */}
          {!isDiscovery && ad.creative && (
            <div>
              <h4 className="text-sm font-semibold text-gray-400 mb-1">Scene Plan</h4>
              <p className="text-white whitespace-pre-wrap text-xs">{ad.creative}</p>
            </div>
          )}

          {/* QA Score — affiliate only */}
          {!isDiscovery && ad.qa_score && (
            <div>
              <h4 className="text-sm font-semibold text-gray-400 mb-1">QA Score</h4>
              <p className="text-white whitespace-pre-wrap text-xs">{ad.qa_score}</p>
            </div>
          )}

          {/* All Images */}
          {ad.images && (
            <div>
              <h4 className="text-sm font-semibold text-gray-400 mb-2">Product Scenes</h4>
              <div className="grid grid-cols-2 gap-2">
                {ad.images.split(",").map((url: string, i: number) => (
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

          {/* Voiceover (if no video) */}
          {(fullAd?.voiceover_url || ad.voiceover_url) && !(fullAd?.video_url || ad.video_url) && (
            <div>
              <h4 className="text-sm font-semibold text-gray-400 mb-2">Voiceover</h4>
              <audio controls className="w-full">
                <source src={fullAd?.voiceover_url ?? ad.voiceover_url ?? ""} type="audio/mpeg" />
              </audio>
            </div>
          )}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-2">
        <button
          onClick={handleReuse}
          className="flex-1 bg-pink-600 hover:bg-pink-500 text-white text-sm font-semibold py-2 px-4 rounded-lg transition-colors"
        >
          Reuse This Ad
        </button>
      </div>
    </div>
  );
}
