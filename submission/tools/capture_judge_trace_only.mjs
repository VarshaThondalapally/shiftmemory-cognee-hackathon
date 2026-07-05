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

const browser = await puppeteer.launch({
  executablePath: chromePath,
  headless: "new",
  defaultViewport: { width: 1280, height: 720 },
  args: ["--disable-gpu", "--hide-scrollbars", "--no-sandbox"],
});

try {
  await fs.mkdir(screenshotDir, { recursive: true });
  const page = await browser.newPage();
  await page.goto("http://127.0.0.1:5173/", { waitUntil: "networkidle2" });
  await page.evaluate(() => window.localStorage.clear());
  await page.reload({ waitUntil: "networkidle2" });
  await waitForText(page, "Each person opens the workspace their role allows", 30000);
  await clickText(page, "button.login-card", "Hackathon judge");
  await waitForText(page, "Memory lifecycle evidence", 60000);
  await waitForText(page, "cognee-cloud", 60000);
  await page.evaluate(() => window.scrollTo(0, 520));
  await new Promise((resolve) => setTimeout(resolve, 1000));
  await page.screenshot({
    path: path.join(screenshotDir, "12_judge_proof_trace.png"),
    fullPage: false,
  });
} finally {
  await browser.close();
}
