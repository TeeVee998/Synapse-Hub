// Playwright Live Interactive Probe Helper
const targetLocator = page.locator("[data-testid='submit-order']");
const isVisible = await targetLocator.isVisible();
const boundingBox = await targetLocator.boundingBox();
console.log({ isVisible, boundingBox });
