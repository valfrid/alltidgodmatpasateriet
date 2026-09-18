const OWNER = "valfrid";
const REPO = "alltidgodmatpasateriet";
const BRANCH = "main";
const RECIPE_DIR = "recipes";

function json(data, status = 200) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "access-control-allow-origin": "*",
      "access-control-allow-headers": "content-type, authorization",
      "access-control-allow-methods": "GET, POST, OPTIONS",
    },
  });
}

function safeFilename(name) {
  if (typeof name !== "string") return null;
  const base = name.trim().replace(/\.md$/i, "");
  if (!/^[a-z0-9][a-z0-9-]*$/i.test(base)) return null;
  return base + ".md";
}

async function github(path, init, token) {
  return fetch("https://api.github.com/repos/" + OWNER + "/" + REPO + path, {
    ...init,
    headers: {
      "accept": "application/vnd.github+json",
      "authorization": "Bearer " + token,
      "x-github-api-version": "2022-11-28",
      "user-agent": "alltidgodmatpasateriet-api",
      ...(init && init.headers ? init.headers : {}),
    },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: json({}).headers });

    if (request.method === "GET" && url.pathname === "/") {
      return json({ ok: true, service: "Alltid God Mat pa Sateriet recipe API" });
    }

    if (request.method === "POST" && url.pathname === "/recipe") {
      if (!env.GITHUB_TOKEN) return json({ error: "GITHUB_TOKEN is not configured" }, 500);

      let body;
      try { body = await request.json(); }
      catch { return json({ error: "Body must be JSON" }, 400); }

      const filename = safeFilename(body.filename);
      if (!filename || typeof body.content !== "string" || !body.content.trim()) {
        return json({ error: "Use { filename: \"recipe-name.md\", content: \"# ...\" }" }, 400);
      }

      const path = RECIPE_DIR + "/" + filename;
      const existing = await github("/contents/" + encodeURIComponent(path) + "?ref=" + BRANCH, { method: "GET" }, env.GITHUB_TOKEN);
      if (existing.status !== 404) {
        if (existing.ok) return json({ error: "Recipe already exists", path }, 409);
        return json({ error: "Could not check existing recipe", status: existing.status }, 502);
      }

      const encoded = btoa(unescape(encodeURIComponent(body.content)));
      const created = await github("/contents/" + encodeURIComponent(path), {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          message: "Add recipe " + filename + " via recipe API",
          content: encoded,
          branch: BRANCH,
        }),
      }, env.GITHUB_TOKEN);

      const result = await created.json().catch(() => ({}));
      if (!created.ok) return json({ error: "GitHub write failed", status: created.status, details: result.message }, 502);
      return json({ ok: true, path, commit: result.commit && result.commit.sha }, 201);
    }

    return json({ error: "Not found" }, 404);
  },
};
