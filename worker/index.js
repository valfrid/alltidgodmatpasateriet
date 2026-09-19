import { createMcpHandler } from "agents/mcp/server";
import { McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";

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
      accept: "application/vnd.github+json",
      authorization: "Bearer " + token,
      "x-github-api-version": "2022-11-28",
      "user-agent": "alltidgodmatpasateriet-api",
      ...(init?.headers || {}),
    },
  });
}

function decodeBase64Utf8(value) {
  const bytes = Uint8Array.from(atob(value.replace(/\n/g, "")), c => c.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

function encodeBase64Utf8(value) {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

function toolText(value) {
  return { content: [{ type: "text", text: typeof value === "string" ? value : JSON.stringify(value, null, 2) }] };
}

async function listRecipes(env) {
  const response = await github("/contents/" + RECIPE_DIR + "?ref=" + BRANCH, { method: "GET" }, env.GITHUB_TOKEN);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error("GitHub list failed: " + response.status);
  return data.filter(item => item.type === "file" && item.name.endsWith(".md")).map(item => item.name);
}

async function getRecipe(env, requestedName) {
  const filename = safeFilename(requestedName);
  if (!filename) throw new Error("Invalid recipe name");
  const path = RECIPE_DIR + "/" + filename;
  const response = await github("/contents/" + encodeURIComponent(path) + "?ref=" + BRANCH, { method: "GET" }, env.GITHUB_TOKEN);
  if (response.status === 404) throw new Error("Recipe not found: " + filename);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error("GitHub read failed: " + response.status);
  return { filename, path, content: decodeBase64Utf8(data.content || ""), sha: data.sha };
}

async function createRecipe(env, requestedName, content) {
  const filename = safeFilename(requestedName);
  if (!filename || typeof content !== "string" || !content.trim()) throw new Error("Invalid filename or empty content");
  const path = RECIPE_DIR + "/" + filename;
  const existing = await github("/contents/" + encodeURIComponent(path) + "?ref=" + BRANCH, { method: "GET" }, env.GITHUB_TOKEN);
  if (existing.ok) throw new Error("Recipe already exists: " + filename);
  if (existing.status !== 404) throw new Error("Could not check existing recipe: " + existing.status);

  const created = await github("/contents/" + encodeURIComponent(path), {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      message: "Add recipe " + filename + " via MCP",
      content: encodeBase64Utf8(content),
      branch: BRANCH,
    }),
  }, env.GITHUB_TOKEN);
  const result = await created.json().catch(() => ({}));
  if (!created.ok) throw new Error("GitHub write failed: " + (result.message || created.status));
  return { ok: true, path, commit: result.commit?.sha };
}

async function deleteRecipe(env, requestedName) {
  const current = await getRecipe(env, requestedName);
  const deleted = await github("/contents/" + encodeURIComponent(current.path), {
    method: "DELETE",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      message: "Delete recipe " + current.filename + " via MCP",
      sha: current.sha,
      branch: BRANCH,
    }),
  }, env.GITHUB_TOKEN);
  const result = await deleted.json().catch(() => ({}));
  if (!deleted.ok) throw new Error("GitHub delete failed: " + (result.message || deleted.status));
  return { ok: true, path: current.path, commit: result.commit?.sha };
}

async function getRecipeSkill(env) {
  const response = await github("/contents/RECIPE_SKILL.md?ref=" + BRANCH, { method: "GET" }, env.GITHUB_TOKEN);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error("GitHub skill read failed: " + response.status);
  return decodeBase64Utf8(data.content || "");
}

async function updateRecipe(env, requestedName, content) {
  const current = await getRecipe(env, requestedName);
  if (typeof content !== "string" || !content.trim()) throw new Error("Content must not be empty");
  const updated = await github("/contents/" + encodeURIComponent(current.path), {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      message: "Update recipe " + current.filename + " via MCP",
      content: encodeBase64Utf8(content),
      sha: current.sha,
      branch: BRANCH,
    }),
  }, env.GITHUB_TOKEN);
  const result = await updated.json().catch(() => ({}));
  if (!updated.ok) throw new Error("GitHub update failed: " + (result.message || updated.status));
  return { ok: true, path: current.path, commit: result.commit?.sha };
}

function createServer(env) {
  const server = new McpServer(
    { name: "Alltid God Mat pa Sateriet", version: "1.3.0" },
    { instructions: "Use the recipe skill for recipe ingestion and editing guidance. Read it with get_recipe_skill when creating or substantially editing a recipe. Before destructive actions, identify the exact recipe first." }
  );

  server.registerTool("list_recipes", {
    description: "List all published recipes in Alltid God Mat pa Sateriet.",
    inputSchema: {},
  }, async () => toolText(await listRecipes(env)));

  server.registerTool("get_recipe", {
    description: "Read one published recipe as Markdown.",
    inputSchema: { filename: z.string().describe("Recipe filename or slug, with or without .md") },
  }, async ({ filename }) => toolText(await getRecipe(env, filename)));

  server.registerTool("create_recipe", {
    description: "Publish a new recipe Markdown file. Fails if the recipe already exists.",
    inputSchema: {
      filename: z.string().describe("Lowercase recipe slug, for example kanelbullar.md"),
      content: z.string().describe("Complete recipe in Markdown"),
    },
  }, async ({ filename, content }) => toolText(await createRecipe(env, filename, content)));

  server.registerTool("get_recipe_skill", {
    description: "Read the current recipe-ingestion skill instructions maintained with the recipe repository.",
    inputSchema: {},
  }, async () => toolText(await getRecipeSkill(env)));

  server.registerTool("delete_recipe", {
    description: "Delete an existing recipe Markdown file. This is destructive; identify the exact recipe before calling it.",
    inputSchema: {
      filename: z.string().describe("Existing recipe filename or slug"),
    },
  }, async ({ filename }) => toolText(await deleteRecipe(env, filename)));

  server.registerTool("update_recipe", {
    description: "Replace the Markdown content of an existing recipe while keeping the same filename.",
    inputSchema: {
      filename: z.string().describe("Existing recipe filename or slug"),
      content: z.string().describe("Complete replacement recipe in Markdown"),
    },
  }, async ({ filename, content }) => toolText(await updateRecipe(env, filename, content)));

  return server;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: json({}).headers });

    if (url.pathname === "/mcp") {
      if (!env.GITHUB_TOKEN) return json({ error: "GITHUB_TOKEN is not configured" }, 500);
      return createMcpHandler(() => createServer(env), { route: "/mcp" })(request, env, ctx);
    }

    if (request.method === "GET" && url.pathname === "/") {
      return json({ ok: true, service: "Alltid God Mat pa Sateriet recipe API", mcp: "/mcp" });
    }

    if (request.method === "POST" && url.pathname === "/recipe") {
      if (!env.GITHUB_TOKEN) return json({ error: "GITHUB_TOKEN is not configured" }, 500);
      let body;
      try { body = await request.json(); }
      catch { return json({ error: "Body must be JSON" }, 400); }

      try {
        const result = await createRecipe(env, body.filename, body.content);
        return json(result, 201);
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        if (message.startsWith("Recipe already exists")) return json({ error: "Recipe already exists" }, 409);
        if (message.startsWith("Invalid")) return json({ error: message }, 400);
        return json({ error: message }, 502);
      }
    }

    return json({ error: "Not found" }, 404);
  },
};