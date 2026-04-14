"use client";
import { useRouter } from "next/navigation";

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
  created_at: string;
};

export default function AdCard({ ad }: { ad: Ad }) {
  const router = useRouter();

  const scoreMatch = ad.qa_score?.match(/\d+/);
  const score = scoreMatch ? scoreMatch[0] : "?";

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
          <span className="bg-pink-600 text-white text-sm font-bold px-3 py-1 rounded-full">
            {score}/10
          </span>
          {ad.compliance_status && (
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
              ad.compliance_status === "PASS"
                ? "bg-green-600/20 text-green-400"
                : "bg-red-600/20 text-red-400"
            }`}>
              {ad.compliance_status === "PASS" ? "Compliant" : "Issues"}
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

      {ad.voiceover_url && (
        <audio controls className="w-full h-8">
          <source src={ad.voiceover_url} type="audio/mpeg" />
        </audio>
      )}

      <button
        onClick={handleReuse}
        className="mt-2 bg-pink-600 hover:bg-pink-500 text-white text-sm font-semibold py-2 px-4 rounded-lg transition-colors"
      >
        Reuse This Ad
      </button>
    </div>
  );
}
