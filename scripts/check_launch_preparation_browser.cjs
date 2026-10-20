/* Run only against an isolated fixture Studio: this exercises preset/restore.
 * node scripts/check_launch_preparation_browser.cjs http://127.0.0.1:8817 <output>
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const base = process.argv[2] || 'http://127.0.0.1:8817';
const out = path.resolve(process.argv[3] || '/tmp/launch-prep-browser');
fs.mkdirSync(out, {recursive:true});
(async () => {
  const browser = await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  try {
    const page = await browser.newPage({viewport:{width:1400,height:1050}});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(base+'/launch-preparation');
    await page.waitForFunction(()=>document.querySelectorAll('#tests tr').length>=30);
    assert.match(await page.locator('#compatibility').textContent(),/matches/);
    assert.equal(await page.locator('#deck-download').isVisible(),false);
    const deckDownload=page.waitForEvent('download');
    await page.locator('#deck').click();
    const deck=await deckDownload;await deck.saveAs(path.join(out,deck.suggestedFilename()));
    assert.match(deck.suggestedFilename(),/Resonance-Mod-Snapshot/);
    const backupDownload=page.waitForEvent('download');
    await page.locator('#backup').click();
    const backup=await backupDownload;const backupPath=path.join(out,backup.suggestedFilename());await backup.saveAs(backupPath);
    await page.locator('#preset').click();
    await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('preset applied'));
    await page.locator('#backup-file').setInputFiles(backupPath);
    await page.waitForFunction(()=>!document.querySelector('#restore').disabled);
    assert.match(await page.locator('#backup-preview').textContent(),/Crystal Fina/);
    await page.locator('#restore').click();
    await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('setup restored'));
    const row=page.locator('tr[data-key="skill-500270"]');
    await row.locator('select[data-field="visuals"]').selectOption('fail');
    await row.locator('select[data-field="sound"]').selectOption('pass');
    await row.locator('textarea').fill('Browser fixture original-enemy observation');
    await page.locator('#save-tests').click();
    await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('observations saved'));
    await page.reload();
    await page.waitForFunction(()=>document.querySelectorAll('#tests tr').length>=30);
    assert.equal(await page.locator('tr[data-key="skill-500270"] select[data-field="visuals"]').inputValue(),'fail');
    await page.locator('#test-filter').fill('Waterga');
    assert.equal(await page.locator('#tests tr:visible').count(),1);
    const sheet=page.waitForEvent('download');await page.locator('a[href="/api/launch/tests.csv"]').click();
    const csv=await sheet;await csv.saveAs(path.join(out,csv.suggestedFilename()));
    assert.match(fs.readFileSync(path.join(out,csv.suggestedFilename()),'utf8'),/Browser fixture/);
    const demoDownload=page.waitForEvent('download');await page.locator('a[href="/api/launch/demo-reference"]').click();
    const demo=await demoDownload;const demoPath=path.join(out,demo.suggestedFilename());await demo.saveAs(demoPath);
    await page.locator('details').filter({has:page.locator('#comparison-file')}).locator('summary').click();
    await page.locator('#comparison-file').setInputFiles(demoPath);
    await page.waitForFunction(()=>!document.querySelector('#comparison-download').hidden);
    assert.equal(JSON.parse(await page.locator('#comparison').textContent()).changedSkills,0);
    await page.locator('#test-filter').fill('');
    await page.screenshot({path:path.join(out,'launch-preparation.png'),fullPage:true});
    assert.deepStrictEqual(errors,[]);
    console.log(JSON.stringify({tests:await page.locator('#tests tr').count(),snapshot:deck.suggestedFilename(),
      backup:backup.suggestedFilename(),restored:true,resultsPersist:true,comparisonUnchanged:true,jsErrors:errors},null,2));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
