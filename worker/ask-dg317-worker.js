/* OPTIONAL: instant AI answers for the Ask A Mechanic box ("DG317").
   Free Cloudflare account -> Workers -> Create -> paste this -> Deploy.
   Settings -> Variables -> add secret ANTHROPIC_API_KEY (from console.anthropic.com).
   Then put the worker URL in DG_CONFIG.aiEndpoint in index.html.
   Cost (Claude Haiku 5.5, Nov 2026 pricing: $0.10 in / $0.50 out per million tokens): about $0.0003 a question,
   so roughly 30 cents per 1,000 questions. Set a monthly spend limit in the Anthropic console (e.g. $5) so a flood can't run up a bill. */
const ALLOWED = ["https://detailguy317.com", "https://www.detailguy317.com"]; // add your GitHub Pages URL if you use it
const SYSTEM = `You are DG317, the shop assistant for the DETAILGUY317 Garage website, answering for an ASE Master
Technician with 25+ years of dealer and OEM experience. Answer like a sharp, friendly master tech:
short, practical, in plain English. Give likely causes in order of probability, what to check first,
and rough DIY difficulty. Flag safety issues clearly (brakes, steering, fuel leaks, overheating,
flashing check-engine light) and tell them to stop driving when appropriate. Never invent part
numbers, TSB numbers or torque specs. If the answer depends on the exact vehicle, say what info
is needed. Keep it under 180 words. If it truly needs hands-on diagnosis, say so and suggest a trusted local shop
(or the dealer for recalls, software updates and key programming). Never promise a personal reply.`;

export default {
  async fetch(req, env) {
    const origin = req.headers.get("Origin") || "";
    const cors = { "Access-Control-Allow-Origin": ALLOWED.includes(origin) ? origin : ALLOWED[0],
                   "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type" };
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    if (req.method !== "POST" || !ALLOWED.includes(origin)) return new Response("no", { status: 403, headers: cors });
    let q = "";
    try { q = String((await req.json()).question || "").slice(0, 1200); } catch (e) {}
    if (q.length < 3) return Response.json({ answer: "Ask me something about your car!" }, { headers: cors });
    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
      body: JSON.stringify({ model: "claude-haiku-5-5", max_tokens: 400, system: SYSTEM,
                             messages: [{ role: "user", content: q }] })
    });
    const j = await r.json();
    const answer = (j.content || []).map(c => c.text || "").join("").trim() || "DG317 is stumped on that one - try adding year/make/model and symptoms.";
    return Response.json({ answer }, { headers: cors });
  }
};
