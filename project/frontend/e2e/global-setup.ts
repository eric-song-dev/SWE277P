import { execFileSync } from "node:child_process";
import path from "node:path";
import type { FullConfig } from "@playwright/test";

// Brings up a separate Compose project (`hub-e2e`: its own containers, network, and volumes) with
// the scripted LLM, creates the "Demo" profile, and returns the teardown that removes it all.

const PROJECT = "hub-e2e";
const PROJECT_DIR = path.resolve(import.meta.dirname, "../..");
const HEALTH_TIMEOUT_MS = 3 * 60_000;
const DEMO_PROFILE = { name: "Demo", preset: "fake", model: "scripted" };

interface Profile {
  id: number;
  name: string;
  preset: string;
}

function composeEnv(port: string): NodeJS.ProcessEnv {
  return {
    ...process.env,
    HUB_HTTP_PORT: port,
    HUB_ENABLE_FAKE_LLM: "true",
    // The shell environment overrides project/.env, so blanking these keeps the stack from
    // seeding the developer's real LLM profile (and its API key).
    LLM_SEED_NAME: "",
    LLM_SEED_PRESET: "",
    LLM_SEED_BASE_URL: "",
    LLM_SEED_MODEL: "",
    LLM_SEED_API_KEY: "",
    LLM_SEED_SHARE_RESULTS: "",
  };
}

// quiet: capture the output instead of printing it; a failure's error still carries it.
function compose(env: NodeJS.ProcessEnv, args: string[], quiet = false) {
  // Only the base file: no COMPOSE_FILE or override can publish the dev ports here.
  execFileSync("docker", ["compose", "-p", PROJECT, "-f", "docker-compose.yml", ...args], {
    cwd: PROJECT_DIR,
    env,
    stdio: quiet ? "pipe" : "inherit",
  });
}

async function waitForHealth(baseURL: string) {
  const deadline = Date.now() + HEALTH_TIMEOUT_MS;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${baseURL}/api/health`);
      if (res.ok) return;
    } catch {
      // nginx or the API is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }
  throw new Error(`${baseURL}/api/health did not answer within ${HEALTH_TIMEOUT_MS / 1000} s`);
}

function send(baseURL: string, method: string, apiPath: string, body?: unknown): Promise<Response> {
  return fetch(`${baseURL}${apiPath}`, {
    method,
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

async function json<T>(res: Response, what: string): Promise<T> {
  if (!res.ok) throw new Error(`${what} failed: ${res.status} ${await res.text()}`);
  return (await res.json()) as T;
}

async function listProfiles(baseURL: string): Promise<Profile[]> {
  return json(await send(baseURL, "GET", "/api/llm-profiles"), "Listing AI profiles");
}

async function createDemoProfile(baseURL: string) {
  const res = await send(baseURL, "POST", "/api/llm-profiles", DEMO_PROFILE);
  let profile: Profile | undefined;
  if (res.status === 409) {
    const body = (await res.json()) as { error?: { code?: string } };
    if (body.error?.code !== "profile_name_taken") throw new Error("Creating the Demo profile failed: 409");
    profile = (await listProfiles(baseURL)).find((p) => p.name === DEMO_PROFILE.name);
  } else {
    profile = await json<Profile>(res, "Creating the Demo profile");
  }
  if (!profile) throw new Error("Could not create or find the Demo profile");
  await json(await send(baseURL, "POST", `/api/llm-profiles/${profile.id}/default`), "Making Demo the default");

  // Only scripted profiles may exist: any other one could send questions to a real provider.
  const others = (await listProfiles(baseURL)).filter((p) => p.preset !== "fake");
  if (others.length > 0) {
    throw new Error(`The e2e stack has non-demo AI profiles: ${others.map((p) => p.name).join(", ")}`);
  }
}

export default async function globalSetup(config: FullConfig) {
  const baseURL = config.projects[0].use.baseURL;
  if (!baseURL) throw new Error("playwright.config.ts must set use.baseURL");
  const env = composeEnv(new URL(baseURL).port);
  const teardown = (quiet = false) => compose(env, ["down", "-v", "--remove-orphans"], quiet);

  // Start clean, even if an interrupted run left the stack behind.
  teardown(true);
  try {
    compose(env, ["up", "-d", "--build"]);
    await waitForHealth(baseURL);
    await createDemoProfile(baseURL);
  } catch (error) {
    teardown();
    throw error;
  }
  return () => teardown();
}
