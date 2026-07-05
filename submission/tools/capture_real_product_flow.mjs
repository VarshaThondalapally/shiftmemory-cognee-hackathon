import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const puppeteerModule = path.join(
  os.tmpdir(),
  "codex-video-tools",
  "node_modules",
  "puppeteer-core",
  "lib",
  "puppeteer",
  "puppeteer-core.js",
);
const { default: puppeteer } = await import(pathToFileURL(puppeteerModule).href);

const repoRoot = path.resolve(import.meta.dirname, "..", "..");
const screenshotDir = path.join(repoRoot, "submission", "real-flow-screenshots");
const chromePath = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const appUrl = "http://127.0.0.1:5173/";
const siteUrl = "http://127.0.0.1:8088/index.html";
const apiUrl = "http://127.0.0.1:8001";

async function resetDemoData() {
  const loginResponse = await fetch(`${apiUrl}/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: "judge-demo", password: "demo" }),
  });
  if (!loginResponse.ok) {
    throw new Error(`Reviewer login failed: ${loginResponse.status}`);
  }
  const session = await loginResponse.json();
  const resetResponse = await fetch(`${apiUrl}/v1/demo/reset`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      "Content-Type": "application/json",
    },
  });
  if (!resetResponse.ok) {
    throw new Error(`Demo reset failed: ${resetResponse.status}`);
  }
}

async function waitForText(page, text, timeout = 60000) {
  await page.waitForFunction(
    (needle) => document.body?.innerText?.includes(needle),
    { timeout },
    text,
  );
}

async function clickText(page, selector, text) {
  const handles = await page.$$(selector);
  for (const handle of handles) {
    const label = await page.evaluate((item) => item.innerText || "", handle);
    if (label.includes(text)) {
      await handle.click();
      return;
    }
  }
  throw new Error(`Could not click ${selector} containing ${text}`);
}

async function screenshot(page, name) {
  await page.screenshot({
    path: path.join(screenshotDir, `${name}.png`),
    fullPage: false,
  });
}

async function signOut(page) {
  const hasSignOut = await page.evaluate(() =>
    Array.from(document.querySelectorAll("button")).some((button) => button.innerText?.includes("Sign out")),
  );
  if (hasSignOut) {
    await clickText(page, "button", "Sign out");
    await waitForText(page, "Each person opens the workspace their role allows", 30000);
  }
}

async function login(page, userName, expectedText) {
  await clickText(page, "button.login-card", userName);
  await waitForText(page, "Sign out", 30000);
  await waitForText(page, expectedText, 60000);
}

async function main() {
  await fs.mkdir(screenshotDir, { recursive: true });
  await resetDemoData();

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: "new",
    defaultViewport: { width: 1280, height: 720 },
    args: ["--disable-gpu", "--hide-scrollbars", "--no-sandbox"],
  });

  const page = await browser.newPage();
  page.setDefaultTimeout(120000);

  try {
    await page.goto(siteUrl, { waitUntil: "networkidle2" });
    await screenshot(page, "01_public_landing");

    await page.goto(appUrl, { waitUntil: "networkidle2" });
    await page.evaluate(() => window.localStorage.clear());
    await page.reload({ waitUntil: "networkidle2" });
    await waitForText(page, "Each person opens the workspace their role allows", 30000);
    await screenshot(page, "02_login_roles");

    await login(page, "Rosa Lee", "Assign shifts before the handoff starts");
    await screenshot(page, "03_supervisor_assignments");

    await signOut(page);
    await login(page, "Nia Brooks", "Save the thing the morning team must not miss");
    await screenshot(page, "04_night_note_empty");
    const note =
      "At 3:18 AM Avery woke twice, asked for water, and settled when the room stayed quiet. Morning lead should watch for tiredness before breakfast.";
    await page.focus("textarea");
    await page.keyboard.type(note, { delay: 2 });
    await clickText(page, "button", "Remember for morning");
    await waitForText(page, "At 3:18 AM Avery woke twice", 150000);
    await screenshot(page, "05_night_note_remembered");

    await signOut(page);
    await login(page, "Omar Chen", "Build the first brief for Avery Johnson");
    await screenshot(page, "06_morning_before_handoff");
    await clickText(page, "button", "Generate handoff");
    await waitForText(page, "Sources used", 180000);
    await screenshot(page, "07_morning_handoff_with_sources");
    await page.evaluate(() => document.querySelector(".ask-form")?.scrollIntoView({ block: "center" }));
    await page.waitForFunction(
      () => {
        const button = Array.from(document.querySelectorAll("button")).find((item) =>
          item.innerText?.includes("Answer from saved notes"),
        );
        return Boolean(button && !button.disabled);
      },
      { timeout: 120000 },
    );
    await page.evaluate(() => {
      const askBox = document.querySelector(".ask-form textarea");
      if (askBox) askBox.value = "";
    });
    await page.focus(".ask-form textarea");
    await page.keyboard.type("What changed after 3 AM?", { delay: 2 });
    await clickText(page, "button", "Answer from saved notes");
    await page.waitForSelector(".answer-panel", { timeout: 180000 });
    await screenshot(page, "08_morning_followup_answer");

    await signOut(page);
    await login(page, "Rosa Lee", "Decide what should keep shaping future handoffs");
    await screenshot(page, "09_supervisor_review_memory");
    await clickText(page, "button", "Keep important");
    await waitForText(page, "important", 120000);
    await screenshot(page, "10_supervisor_improve_memory");

    await signOut(page);
    await login(page, "Demo reviewer", "Memory lifecycle evidence");
    await waitForText(page, "cognee-cloud", 60000);
    await screenshot(page, "11_judge_proof_top");
    await page.evaluate(() => window.scrollTo(0, 520));
    await new Promise((resolve) => setTimeout(resolve, 1000));
    await screenshot(page, "12_judge_proof_trace");
  } finally {
    await browser.close();
  }

  console.log(`Saved real product flow screenshots to ${screenshotDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
