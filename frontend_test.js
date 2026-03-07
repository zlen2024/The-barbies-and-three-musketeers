const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();

    await page.goto('http://localhost:5173/forecast?location=ALL&sku=ALL');

    // Attempt to evaluate or at least screenshot to ensure it renders
    await page.waitForTimeout(5000);
    await page.screenshot({ path: 'forecast_test.png' });

    console.log('Test completed.');
    await browser.close();
})();
