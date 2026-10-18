/* Browser regression checks. Requires Playwright, Chromium and a running Studio
 * with the optional FFBE library already installed. Never starts a download.
 * node scripts/check_ffbe_library_browser.cjs http://127.0.0.1:8814 /tmp/previews
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const base = process.argv[2] || 'http://127.0.0.1:8814';
const output = process.argv[3];
(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    headless: true, args: ['--no-sandbox'],
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1380, height: 960 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(base + '/ffbe-animation-library');
    await page.waitForSelector('#workspace:not([hidden])', { timeout: 90000 });
    await page.waitForFunction(() => document.querySelectorAll('#source option').length > 3000);
    async function choose(source) {
      const pending = page.waitForResponse(r => r.url().includes('/api/ffbe-library/catalog?') &&
        new URL(r.url()).searchParams.get('source') === source);
      await page.selectOption('#source', source);
      const data = await (await pending).json();
      await page.waitForFunction(total => document.querySelector('#pageCount').textContent.endsWith('of ' + total.toLocaleString()), data.total);
      return data;
    }
    await page.fill('#source-search', 'Agrias');
    if (await page.locator('#source option').count() !== 3) throw Error('Source-name narrowing failed');
    let result = await choose('character:Agrias');
    if (!result.items.every(r => r.sourceLabel === 'Agrias')) throw Error('Wrong owner in results');
    if (!result.items.some(r => r.name === 'Cura')) throw Error('Shared Cura omitted');
    await page.locator('#list .entry').filter({ hasText: 'Cura' }).first().click();
    await page.waitForFunction(() => state.detail?.entry.name === 'Cura');
    if (!(await page.locator('#metadata').textContent()).includes('Source: Agrias')) throw Error('Wrong shared-spell owner');
    await page.waitForFunction(() => !document.querySelector('#play').disabled, null, { timeout: 90000 });
    if (output) {
      fs.mkdirSync(output, { recursive: true });
      await page.screenshot({ path: path.join(output, 'source-filter-agrias.png'), fullPage: true });
    }
    await page.click('#play');
    await page.fill('#source-search', 'Cactuar');
    result = await choose('monster:Cactuar');
    if (await page.evaluate(() => state.playing || state.detail !== null)) throw Error('Previous preview remained active');
    if (!result.items.every(r => r.sourceLabel === 'Cactuar' && r.kind === 'monster')) throw Error('Wrong monster source');
    await page.check('#includeEmpty');
    await page.fill('#source-search', 'Warrior of Light');
    result = await choose('character:Warrior of Light');
    if (result.total <= 60) throw Error('Pagination fixture changed');
    await page.click('#next');
    await page.waitForFunction(() => document.querySelector('#pageCount').textContent.startsWith('61'));
    await page.fill('#source-search', 'Agrias');
    await choose('character:Agrias');
    if (!(await page.locator('#pageCount').textContent()).startsWith('1')) throw Error('Source change retained pagination');
    result = await choose('');
    if (result.total !== 45478 || await page.locator('#source-search').inputValue()) throw Error('All sources did not clear filter');
    await page.evaluate(async () => await select({ kind: 'ability', id: '228600', key: 'ability:228600',
      name: 'Snowstorm', sourceLabel: 'Unei', sourceType: 'character' }));
    const snowstorm = await page.evaluate(() => {
      state.position = 2; draw(2);
      return { effects: Object.keys(state.effects), warnings: document.querySelector('#warnings').textContent,
        screen: spritesAt(2).filter(s => s.screen).length,
        rear: spritesAt(2).filter(s => s.rear).length };
    });
    if (snowstorm.effects.length !== 4 || snowstorm.warnings || !snowstorm.screen || !snowstorm.rear) throw Error('Snowstorm layers unavailable');
    if (output) await page.screenshot({ path: path.join(output, 'snowstorm-layering.png'), fullPage: true });
    // Deliberately put a foreground effect first in the source timeline. Pixel
    // results must show rear red, then green actors, then a half-alpha blue hit.
    const pixels = await page.evaluate(async () => {
      async function solid(color) {
        const c = document.createElement('canvas'); c.width = c.height = 2;
        const x = c.getContext('2d'); x.fillStyle = color; x.fillRect(0, 0, 2, 2);
        const image = new Image(); await new Promise(resolve => { image.onload = resolve; image.src = c.toDataURL(); });
        return image;
      }
      imageCache.set('rear-test', await solid('#ff0000'));
      imageCache.set('front-test', await solid('#0000ff'));
      const event = id => ({ frame: 0, effectId: id, flags: [] });
      state.detail = { entry: {}, effects: { front: { scale: 1 }, rear: { scale: 1 } }, variants: [[
        { frame: 0, flags: ['1', '1'], effects: [event('front')] },
        { frame: 0, flags: ['2', '1'], effects: [event('rear')] },
      ]] };
      const simulation = (url, scale, alpha) => ({ textures: [{ url }], frames: [[
        { tex: 0, pos: [0, 0, 0], scale, alpha, color: [1, 1, 1], blend: 'normal' },
      ]] });
      state.effects = { front: simulation('front-test', [200, 200], .5), rear: simulation('rear-test', [2000, 2000], 1) };
      state.bounds = { x: 0, y: 0, scale: 1 };
      document.querySelector('#zoom').value = 1; document.querySelector('#caster').value = 'character';
      drawActor = (kind, x, y, time, point) => {
        const [px, py] = point(x, y); ctx.fillStyle = '#00ff00'; ctx.fillRect(px - 40, py - 40, 80, 80);
      };
      draw(0);
      return { target: [...ctx.getImageData(260, 330, 1, 1).data],
        caster: [...ctx.getImageData(700, 330, 1, 1).data], rear: [...ctx.getImageData(480, 550, 1, 1).data] };
    });
    if (pixels.target[0] || Math.abs(pixels.target[1] - 127) > 1 || Math.abs(pixels.target[2] - 128) > 1 ||
      pixels.caster.join() !== '0,255,0,255' || pixels.rear.join() !== '255,0,0,255') throw Error('Incorrect compositing ' + JSON.stringify(pixels));
    if (errors.length) throw Error(errors.join('\n'));
    console.log(JSON.stringify({ sources: 3370, snowstorm, pixels, errors }, null, 2));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
