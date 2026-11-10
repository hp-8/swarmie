#!/usr/bin/env node
// Submit every URL in the live sitemap to IndexNow (Bing, Yandex, Seznam, Naver...).
// Usage: node indexnow.mjs https://example.com <key>
// Requires https://example.com/<key>.txt to be live and contain the key.
const [site, key] = process.argv.slice(2);
if (!site || !key) {
  console.error("usage: node indexnow.mjs https://example.com <key>");
  process.exit(2);
}
const origin = site.replace(/\/$/, "");
const host = new URL(origin).host;

const keyRes = await fetch(`${origin}/${key}.txt`);
if (!keyRes.ok || (await keyRes.text()).trim() !== key) {
  console.error(`key file ${origin}/${key}.txt missing or wrong; deploy it first`);
  process.exit(1);
}

const xml = await (await fetch(`${origin}/sitemap.xml`)).text();
const urlList = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1].trim()).filter((u) => new URL(u).host === host);
if (!urlList.length) {
  console.error("no URLs for this host in sitemap.xml");
  process.exit(1);
}

const res = await fetch("https://api.indexnow.org/indexnow", {
  method: "POST",
  headers: { "Content-Type": "application/json; charset=utf-8" },
  body: JSON.stringify({ host, key, keyLocation: `${origin}/${key}.txt`, urlList }),
});
console.log(`IndexNow: ${res.status} ${res.statusText} for ${urlList.length} URLs`);
process.exit(res.ok ? 0 : 1);
