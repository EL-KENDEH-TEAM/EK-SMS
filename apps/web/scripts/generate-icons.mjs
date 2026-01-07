/**
 * PWA Icon Generator Script
 *
 * Generates PNG icons in various sizes from the SVG source.
 *
 * Usage:
 *   pnpm add -D sharp
 *   node scripts/generate-icons.mjs
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];
const iconsDir = join(__dirname, '../public/icons');

async function generateIcons() {
  try {
    // Dynamic import of sharp
    const sharp = (await import('sharp')).default;

    const svgPath = join(iconsDir, 'icon.svg');

    if (!existsSync(svgPath)) {
      console.error('Error: icon.svg not found in public/icons/');
      process.exit(1);
    }

    const svgBuffer = readFileSync(svgPath);

    console.log('Generating PWA icons...\n');

    for (const size of sizes) {
      const outputPath = join(iconsDir, `icon-${size}x${size}.png`);

      await sharp(svgBuffer)
        .resize(size, size)
        .png()
        .toFile(outputPath);

      console.log(`  Created: icon-${size}x${size}.png`);
    }

    // Also create favicon.ico (using 32x32)
    const faviconPath = join(__dirname, '../public/favicon.ico');
    await sharp(svgBuffer)
      .resize(32, 32)
      .png()
      .toFile(faviconPath.replace('.ico', '.png'));

    console.log('  Created: favicon.png');
    console.log('\nAll icons generated successfully!');
    console.log('\nNote: For favicon.ico, you may want to convert favicon.png to .ico format');
    console.log('using an online converter or the "png-to-ico" package.');

  } catch (error) {
    if (error.code === 'ERR_MODULE_NOT_FOUND' || error.message?.includes('sharp')) {
      console.error('Error: sharp is not installed.');
      console.error('Please run: pnpm add -D sharp');
      console.error('Then run this script again: node scripts/generate-icons.mjs');
    } else {
      console.error('Error generating icons:', error);
    }
    process.exit(1);
  }
}

generateIcons();
