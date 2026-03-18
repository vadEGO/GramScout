import { useEffect, useState } from "react";

const API = "/api/v1";

interface Prompt {
  id: string;
  name: string;
  tone: string;
  use_case: string;
  system_prompt: string;
  user_prompt_template: string;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
  version: number;
}

const BUILT_IN_PROMPTS: Omit<Prompt, "id" | "version">[] = [
  {
    name: "Hater",
    tone: "Critical, dismissive, arrogant",
    use_case: "Provokes clicks from curious readers",
    system_prompt: "You are a skeptical Telegram user. Write a short critical or dismissive comment about this post. Be blunt and slightly arrogant. 15-30 words.",
    user_prompt_template: "Post: {post_text}\nWrite a hater comment:",
    temperature: 0.8,
    max_tokens: 50,
    is_active: true,
  },
  {
    name: "Flirty",
    tone: "Playful, suggestive",
    use_case: "18+ channels, dating niches",
    system_prompt: "You are a flirty Telegram user. Write a playful, slightly suggestive comment. Keep it short and charming. 15-30 words.",
    user_prompt_template: "Post: {post_text}\nWrite a flirty comment:",
    temperature: 0.9,
    max_tokens: 50,
    is_active: true,
  },
  {
    name: "Expert",
    tone: "Knowledgeable, helpful",
    use_case: "Crypto, finance, education",
    system_prompt: "You are an expert in this topic. Add a helpful insight or correction. Sound knowledgeable but not preachy. 15-35 words.",
    user_prompt_template: "Post: {post_text}\nWrite an expert comment:",
    temperature: 0.6,
    max_tokens: 60,
    is_active: true,
  },
  {
    name: "Question",
    tone: "Curious, engaging",
    use_case: "Increases comment thread activity",
    system_prompt: "You are a curious person. Ask an interesting question about this post that others would want to answer. 10-25 words.",
    user_prompt_template: "Post: {post_text}\nWrite a question comment:",
    temperature: 0.75,
    max_tokens: 40,
    is_active: true,
  },
  {
    name: "Controversial",
    tone: "Polarizing opinion",
    use_case: "Drives debate and profile clicks",
    system_prompt: "You have a strong, controversial opinion about this post. State it boldly. Be polarizing but not offensive. 15-30 words.",
    user_prompt_template: "Post: {post_text}\nWrite a controversial comment:",
    temperature: 0.85,
    max_tokens: 50,
    is_active: true,
  },
  {
    name: "Supportive",
    tone: "Agreeable, encouraging",
    use_case: "Builds positive presence",
    system_prompt: "You strongly agree with this post. Write a supportive, enthusiastic comment. 10-25 words.",
    user_prompt_template: "Post: {post_text}\nWrite a supportive comment:",
    temperature: 0.7,
    max_tokens: 40,
    is_active: true,
  },
];

export default function Prompts() {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [selected, setSelected] = useState<Prompt | null>(null);
  const [preview, setPreview] = useState("");
  const [testPost, setTestPost] = useState("");

  useEffect(() => {
    setPrompts(
      BUILT_IN_PROMPTS.map((p, i) => ({ ...p, id: `builtin-${i}`, version: 1 }))
    );
  }, []);

  const testPrompt = async (prompt: Prompt) => {
    if (!testPost.trim()) return;
    setPreview("Generating...");
    // In production, this calls the API
    setTimeout(() => {
      setPreview(
        `[Preview of "${prompt.name}" prompt with temp=${prompt.temperature}]\n\n` +
          `System: ${prompt.system_prompt.slice(0, 100)}...\n\n` +
          `Input: ${testPost.slice(0, 80)}...`
      );
    }, 500);
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Prompt Templates</h2>
        <span className="text-sm text-gray-500">{prompts.length} templates</span>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-1 space-y-3">
          {prompts.map((p) => (
            <div
              key={p.id}
              onClick={() => setSelected(p)}
              className={`p-4 rounded-lg border cursor-pointer transition-all ${
                selected?.id === p.id
                  ? "bg-primary-600/20 border-primary-500"
                  : "bg-dark-800 border-gray-800 hover:border-gray-700"
              }`}
            >
              <div className="flex justify-between items-start">
                <div>
                  <div className="font-semibold">{p.name}</div>
                  <div className="text-xs text-gray-500 mt-1">{p.use_case}</div>
                </div>
                <span
                  className={`px-2 py-0.5 rounded text-xs ${
                    p.is_active ? "bg-green-600" : "bg-gray-600"
                  }`}
                >
                  {p.is_active ? "Active" : "Off"}
                </span>
              </div>
              <div className="mt-2 flex gap-3 text-xs text-gray-500">
                <span>temp: {p.temperature}</span>
                <span>tokens: {p.max_tokens}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="col-span-2">
          {selected ? (
            <div className="bg-dark-800 rounded-lg border border-gray-800 p-6">
              <h3 className="text-lg font-semibold mb-4">{selected.name}</h3>

              <div className="space-y-4">
                <div>
                  <label className="text-sm text-gray-400 block mb-1">Tone</label>
                  <div className="text-sm">{selected.tone}</div>
                </div>

                <div>
                  <label className="text-sm text-gray-400 block mb-1">Use Case</label>
                  <div className="text-sm">{selected.use_case}</div>
                </div>

                <div>
                  <label className="text-sm text-gray-400 block mb-1">System Prompt</label>
                  <div className="bg-dark-900 rounded p-3 text-sm font-mono text-gray-300">
                    {selected.system_prompt}
                  </div>
                </div>

                <div>
                  <label className="text-sm text-gray-400 block mb-1">User Template</label>
                  <div className="bg-dark-900 rounded p-3 text-sm font-mono text-gray-300">
                    {selected.user_prompt_template}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-400 block mb-1">Temperature</label>
                    <input
                      type="range"
                      min="0"
                      max="1.2"
                      step="0.05"
                      value={selected.temperature}
                      readOnly
                      className="w-full"
                    />
                    <span className="text-sm text-primary-400">{selected.temperature}</span>
                  </div>
                  <div>
                    <label className="text-sm text-gray-400 block mb-1">Max Tokens</label>
                    <div className="text-sm">{selected.max_tokens}</div>
                  </div>
                </div>

                <div className="border-t border-gray-700 pt-4">
                  <label className="text-sm text-gray-400 block mb-2">Test with a post</label>
                  <textarea
                    value={testPost}
                    onChange={(e) => setTestPost(e.target.value)}
                    placeholder="Paste a post text here to preview the prompt..."
                    className="w-full bg-dark-900 border border-gray-700 rounded px-3 py-2 text-sm h-20 resize-none focus:outline-none focus:border-primary-500"
                  />
                  <button
                    onClick={() => testPrompt(selected)}
                    disabled={!testPost.trim()}
                    className="mt-2 px-4 py-1.5 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-700 disabled:text-gray-500 rounded text-sm transition-colors"
                  >
                    Preview Prompt
                  </button>
                  {preview && (
                    <div className="mt-3 bg-dark-900 rounded p-3 text-xs font-mono text-gray-400 whitespace-pre-wrap">
                      {preview}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-dark-800 rounded-lg border border-gray-800 p-12 text-center">
              <div className="text-4xl mb-4">✏️</div>
              <div className="text-gray-500">Select a prompt template to view details</div>
              <div className="text-xs text-gray-600 mt-2">
                These templates control how AI generates comments for different tones and strategies
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
