import Phaser from 'phaser';

type G = Phaser.GameObjects.Graphics;

function tower(g: G, x: number, top: number, w: number, base: number, k: number, roofColor: number) {
  g.fillStyle(0xc9c9d6, 1);
  g.fillRect(x, top, w, base - top);
  g.fillStyle(0xaaaabb, 1);
  for (let i = 0; i < 3; i++) g.fillRect(x + (i * w) / 3 + 2 * k, top - 12 * k, w / 3 - 4 * k, 12 * k);
  g.fillStyle(roofColor, 1);
  g.fillTriangle(x - 8 * k, top - 12 * k, x + w + 8 * k, top - 12 * k, x + w / 2, top - 67 * k);
}

export function drawCastle(g: G, cx: number, base: number, k = 1) {
  const L = cx - 175 * k, R = cx + 105 * k, C = cx - 45 * k;
  g.fillStyle(0xd7d7e3, 1);
  g.fillRect(cx - 140 * k, base - 120 * k, 280 * k, 120 * k);
  g.fillStyle(0xbbbbcc, 1);
  for (let i = 0; i < 8; i++) g.fillRect(cx - 140 * k + i * 35 * k + 4 * k, base - 132 * k, 27 * k, 12 * k);
  tower(g, L, base - 190 * k, 70 * k, base, k, 0x3a6ea5);
  tower(g, R, base - 190 * k, 70 * k, base, k, 0x3a6ea5);
  tower(g, C, base - 250 * k, 90 * k, base, k, 0xc0392b);
  g.lineStyle(3, 0x553311, 1);
  g.lineBetween(C + 45 * k, base - 317 * k, C + 45 * k, base - 347 * k);
  g.fillStyle(0xe63946, 1);
  g.fillTriangle(C + 45 * k, base - 347 * k, C + 73 * k, base - 339 * k, C + 45 * k, base - 331 * k);
  g.fillStyle(0x6b4423, 1);
  g.fillRect(cx - 28 * k, base - 75 * k, 56 * k, 75 * k);
  g.fillCircle(cx, base - 75 * k, 28 * k);
  g.fillStyle(0x2d2d44, 1);
  [[L + 27 * k, base - 150 * k], [R + 27 * k, base - 150 * k], [C + 37 * k, base - 200 * k]].forEach(([x, y]) => g.fillRect(x, y, 16 * k, 26 * k));
}

/** Décor : ciel, collines, château. opaque = écran d'explication ; sinon on voit la caméra à travers. */
export function drawBackdrop(s: Phaser.Scene, opaque = false) {
  const w = s.scale.width, h = s.scale.height;
  const g = s.add.graphics().setDepth(-10);
  if (opaque) {
    g.fillGradientStyle(0x6ec6ff, 0x6ec6ff, 0xdff3ff, 0xdff3ff, 1);
    g.fillRect(0, 0, w, h);
    g.fillStyle(0xffe066, 1);
    g.fillCircle(850, 120, 55);
    g.fillStyle(0xffffff, 0.9);
    [[160, 130], [470, 190], [700, 150]].forEach(([x, y]) => { g.fillCircle(x, y, 32); g.fillCircle(x + 35, y + 8, 26); g.fillCircle(x - 35, y + 10, 24); });
    g.fillStyle(0x5cb85c, 1);
    g.fillEllipse(180, h, 700, 220);
    g.fillEllipse(800, h, 700, 260);
    g.fillStyle(0x4aa24a, 1);
    g.fillRect(0, h - 70, w, 70);
    drawCastle(g, w / 2, h - 70, 1);
  } else {
    // en jeu : on garde la caméra visible, le château veille dans le coin
    g.fillStyle(0x4aa24a, 0.95);
    g.fillRect(0, h - 40, w, 40);
    drawCastle(g, 150, h - 40, 0.5);
  }
}

export type KidPose = 'right' | 'left' | 'both' | 'head' | 'duck' | 'still';

/** Petit personnage vu de face, comme dans un miroir : « right » = bras à droite sur l'écran. */
export function drawKid(g: G, cx: number, cy: number, k: number, pose: KidPose) {
  if (pose === 'duck') { cy += 50 * k; k *= 0.75; }
  g.lineStyle(8, 0x1d2b53, 1);
  g.lineBetween(cx, cy - 48 * k, cx, cy + 30 * k);
  g.lineBetween(cx, cy + 30 * k, cx - 25 * k, cy + 85 * k);
  g.lineBetween(cx, cy + 30 * k, cx + 25 * k, cy + 85 * k);
  const arm = (side: number, up: boolean, onHead = false) => {
    const x = onHead ? cx + side * 16 * k : cx + side * (up ? 40 : 32) * k;
    const y = onHead ? cy - 88 * k : cy + (up ? -100 : 10) * k;
    g.lineBetween(cx, cy - 35 * k, x, y);
    if (up) { g.fillStyle(0xffd23f, 1); g.fillCircle(x, y - 10 * k, 9 * k); }
  };
  arm(-1, pose === 'left' || pose === 'both');
  arm(1, pose === 'right' || pose === 'both', pose === 'head');
  g.fillStyle(0xffd9b3, 1);
  g.fillCircle(cx, cy - 70 * k, 22 * k);
  g.lineStyle(4, 0x1d2b53, 1);
  g.strokeCircle(cx, cy - 70 * k, 22 * k);
  if (pose === 'head') { g.fillStyle(0xffd23f, 1); g.fillRect(cx - 14 * k, cy - 100 * k, 28 * k, 10 * k); }
}

/**
 * Dessine la zone initiale de cadrage (silhouette guide debout / assis)
 * au-dessus du flux caméra pendant le calibrage ou le départ.
 */
export function drawInitialZone(
  g: G,
  cx: number,
  cy: number,
  posture: 'standing' | 'sitting',
  inZone = false
) {
  g.clear();
  const color = inZone ? 0x2e9e5b : 0xffd23f;
  const alpha = inZone ? 0.95 : 0.65;
  const bgAlpha = inZone ? 0.16 : 0.08;

  const bw = posture === 'sitting' ? 360 : 310;
  const bh = posture === 'sitting' ? 380 : 490;
  const by = posture === 'sitting' ? cy - 20 : cy;

  g.fillStyle(color, bgAlpha);
  g.fillRoundedRect(cx - bw / 2, by - bh / 2, bw, bh, 24);
  g.lineStyle(4, color, alpha);
  g.strokeRoundedRect(cx - bw / 2, by - bh / 2, bw, bh, 24);

  // Guide tête
  const headY = by - bh / 2 + 65;
  g.strokeCircle(cx, headY, 44);

  // Guide épaules & torse
  const shY = headY + 70;
  const shW = posture === 'sitting' ? 135 : 115;
  g.lineBetween(cx - shW, shY, cx + shW, shY);
  g.lineBetween(cx - shW, shY, cx - shW + 20, by + bh / 2 - (posture === 'sitting' ? 85 : 180));
  g.lineBetween(cx + shW, shY, cx + shW - 20, by + bh / 2 - (posture === 'sitting' ? 85 : 180));

  if (posture === 'sitting') {
    // Esquisse de chaise sous le torse
    const chairY = by + bh / 2 - 35;
    g.lineBetween(cx - 130, chairY, cx + 130, chairY);
    g.lineBetween(cx - 100, chairY, cx - 110, chairY + 25);
    g.lineBetween(cx + 100, chairY, cx + 110, chairY + 25);
  } else {
    // Guide jambes debout
    const hipY = by + 70;
    g.lineBetween(cx, hipY, cx - 40, by + bh / 2 - 20);
    g.lineBetween(cx, hipY, cx + 40, by + bh / 2 - 20);
  }
}