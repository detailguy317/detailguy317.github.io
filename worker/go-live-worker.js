/* DG317 "GO LIVE" helper - lets admin.html save data/live-content.js to GitHub for you (no copy/paste).
   Free Cloudflare account -> Workers & Pages -> Create -> Worker -> name it dg317-golive -> Deploy -> Edit code ->
   paste ALL of this file -> Deploy. Then Settings -> Variables and Secrets -> add these as type "Secret":
     GITHUB_TOKEN   = a fine-grained GitHub token: github.com -> Settings -> Developer settings -> Fine-grained tokens ->
                      Generate -> Repository access: ONLY detailguy317.github.io -> Permissions: Contents = Read and write.
     ADMIN_PASSWORD = any long password you make up (you type it once into admin.html on your computer/phone).
   Copy the worker's URL (like https://dg317-golive.yourname.workers.dev) into admin.html -> GO LIVE settings.
   It can ONLY change data/live-content.js, and only with your password. */
const REPO = "detailguy317/detailguy317.github.io";
const FILE = "data/live-content.js";
const BRANCH = "main";
const ALLOWED = ["https://detailguy317.com", "https://www.detailguy317.com", "https://detailguy317.github.io"];

export default {
  async fetch(req, env) {
    const origin = req.headers.get("Origin") || "";
    const cors = { "Access-Control-Allow-Origin": ALLOWED.includes(origin) ? origin : ALLOWED[0],
                   "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type" };
    const out = (obj, status = 200) => new Response(JSON.stringify(obj), { status, headers: { ...cors, "Content-Type": "application/json" } });
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    if (req.method !== "POST" || !ALLOWED.includes(origin)) return out({ ok: false, error: "Not allowed from here." }, 403);

    let body = {};
    try { body = await req.json(); } catch (e) { return out({ ok: false, error: "Bad request." }, 400); }
    if (!env.ADMIN_PASSWORD || !env.GITHUB_TOKEN) return out({ ok: false, error: "Worker secrets not set yet (GITHUB_TOKEN / ADMIN_PASSWORD)." }, 500);
    await new Promise(r => setTimeout(r, 400));                       // slows down password guessing
    if (String(body.password || "") !== env.ADMIN_PASSWORD) return out({ ok: false, error: "Wrong password." }, 401);

    const content = String(body.content || "");
    if (content.length > 300000 || !content.includes("window.DG_LIVE = ") || !content.trim().endsWith(";"))
      return out({ ok: false, error: "That doesn't look like a live-content.js file - nothing was saved." }, 400);
    try { JSON.parse(content.slice(content.indexOf("window.DG_LIVE = ") + 17).trim().replace(/;\s*$/, "")); }
    catch (e) { return out({ ok: false, error: "The file has a typo in it - nothing was saved." }, 400); }

    const gh = (path, init = {}) => fetch("https://api.github.com/repos/" + REPO + "/contents/" + path, {
      ...init, headers: { "Authorization": "Bearer " + env.GITHUB_TOKEN, "Accept": "application/vnd.github+json",
                          "User-Agent": "dg317-golive", "X-GitHub-Api-Version": "2022-11-28", ...(init.headers || {}) } });
    const cur = await gh(FILE + "?ref=" + BRANCH);
    if (!cur.ok) return out({ ok: false, error: "GitHub said " + cur.status + " - check the token's repo access." }, 502);
    const sha = (await cur.json()).sha;
    const bytes = new TextEncoder().encode(content); let bin = "";
    for (let i = 0; i < bytes.length; i += 8192) bin += String.fromCharCode(...bytes.subarray(i, i + 8192));
    const b64 = btoa(bin);
    const put = await gh(FILE, { method: "PUT", body: JSON.stringify({
      message: "GO LIVE: " + String(body.note || "racing update").slice(0, 80), content: b64, sha, branch: BRANCH,
      committer: { name: "dg317-golive", email: "dg317-golive@users.noreply.github.com" } }) });
    if (!put.ok) return out({ ok: false, error: "GitHub said " + put.status + " - try again in a minute." }, 502);
    return out({ ok: true, commit: ((await put.json()).commit || {}).sha || "" });
  }
};
