import Phaser from 'phaser';
import { drawKid, type KidPose } from './castle';
import type { Kind } from '../core/metrics';
import { speak, stopSpeech } from './speech';
import { PRESCRIPTION } from '../platform';

type GoKind = Exclude<Kind, 'enemy'>;

interface GestureDef {
  kind: GoKind;
  emoji: string;
  name: string;
  action: string;
  desc: string;
  kid: KidPose;
  imageKey: string;
}

interface TutorialSlide {
  title: string;
  text: string;
  imageKey?: string;  // character doing the gesture (left)
  badgeKey?: string;  // creature mascot to recognise (right)
}

const GESTURE_OPTIONS: GestureDef[] = [
  {
    kind: 'fairy_r',
    emoji: '🔵🧚',
    name: 'Blue Fairy',
    action: 'Right arm',
    desc: 'Quickly raise your RIGHT ARM!\n\nLike in a mirror: your right arm is on the right of the screen.',
    kid: 'right',
    imageKey: 'sel_fairy_r',
  },
  {
    kind: 'fairy_l',
    emoji: '💗🧚',
    name: 'Pink Fairy',
    action: 'Left arm',
    desc: 'Quickly raise your LEFT ARM!\n\nYour left arm is on the left of the screen.',
    kid: 'left',
    imageKey: 'sel_fairy_l',
  },
  {
    kind: 'star',
    emoji: '⭐',
    name: 'Shooting Star',
    action: 'Both arms',
    desc: 'Raise BOTH arms high, like a big star!',
    kid: 'both',
    imageKey: 'sel_star',
  },
  {
    kind: 'crown',
    emoji: '👑',
    name: 'Crown',
    action: 'Hand on head',
    desc: 'Quickly put a hand on your head to wear the crown!',
    kid: 'head',
    imageKey: 'sel_crown',
  },
  {
    kind: 'dragon',
    emoji: '🐉',
    name: 'Dragon',
    action: 'Duck!',
    desc: 'Duck down quickly (crouch) to hide from the dragon, then stand back up!',
    kid: 'duck',
    imageKey: 'sel_dragon',
  },
];

const COLORS = {
  ink: '#1d2b53',
  purple: 0x7654d8,
  lavender: 0xf1edff,
  blue: 0xe8f3ff,
  pink: 0xffedf5,
  mint: 0xe7f8ef,
  gold: 0xffd23f,
};

export class IntroScene extends Phaser.Scene {
  private step = 0;
  private prescribed = PRESCRIPTION.kinds as GoKind[] | null;
  private selected: GoKind[] = this.prescribed ? [...this.prescribed] : ['fairy_r', 'fairy_l', 'star'];
  private ui: Phaser.GameObjects.GameObject[] = [];
  private kidG!: Phaser.GameObjects.Graphics;

  constructor() {
    super('intro');
  }

  preload() {
    this.load.image('mascot', '/assets_flat/sensai-mascot-nobg.png');
    this.load.image('card_mouvement', '/Assets/gardien%20chateau/Energetic%20Boy%20on%20Motion%20Platform.png');
    this.load.image('card_precision', '/Assets/gardien%20chateau/Cheerful%20Bullseye%20Adventure.png');
    this.load.image('card_statue', '/Assets/gardien%20chateau/Cheerful%20Blue%20Mascot%20on%20Sparkling%20Pedestal.png');

    this.load.image('sel_fairy_r', '/Assets/gardien%20chateau/Fairy%20Mascot%20and%20Glossy%20Blue%20Orb.png');
    this.load.image('sel_fairy_l', '/Assets/gardien%20chateau/Kawaii%20Fairy%20with%20Sparkling%20Heart.png');
    this.load.image('sel_star', '/Assets/gardien%20chateau/Glossy%20Fairy%20Hugging%20a%20Golden%20Star.png');
    this.load.image('sel_crown', '/Assets/gardien%20chateau/Crowned%20Purple%20Mascot%20with%20Sparkles.png');
    this.load.image('sel_dragon', '/Assets/gardien%20chateau/Joyful%20Mint%20Baby%20Dragon%20in%20Flight.png');
    this.load.image('sel_ogre', '/Assets/gardien%20chateau/Cute%20Chibi%20Ogre%20with%20Spiked%20Club.png');

    this.load.image('tut_boy_finger', '/Assets/gardien%20chateau/Cheerful%20Boy%20with%20Raised%20Finger.png');
    this.load.image('tut_boy_green', '/Assets/gardien%20chateau/Cheerful%20Boy%20in%20Green%20Hoodie.png');
    this.load.image('tut_boy_purple', '/Assets/gardien%20chateau/Cheerful%20Purple%20Hoodie%20Boy.png');
    this.load.image('tut_girl_pink', '/Assets/gardien%20chateau/Joyful%20Pink%20Tracksuit%20Girl%20Pointing%20Up.png');
    this.load.image('tut_girl_red', '/Assets/gardien%20chateau/Adorable%20Red%20Tracksuit%20Chibi%20Girl.png');
    this.load.image('tut_chibi_crouch', '/Assets/gardien%20chateau/Chibi%20Girl%20Crouching%20and%20Cheering.png');
  }

  create() {
    this.kidG = this.add.graphics().setDepth(1);
    this.render();
  }

  private text(
    x: number,
    y: number,
    value: string,
    style: Phaser.Types.GameObjects.Text.TextStyle = {},
  ) {
    const label = this.add.text(x, y, value, {
      fontFamily: 'Outfit, "Trebuchet MS", Arial, sans-serif',
      color: COLORS.ink,
      ...style,
    });
    this.ui.push(label);
    return label;
  }

  private drawSparkle(x: number, y: number, size: number, color = 0xffd23f, alpha = 0.95) {
    const g = this.add.graphics();
    g.fillStyle(color, alpha);
    g.beginPath();
    const inner = size * 0.22;
    for (let i = 0; i < 8; i++) {
      const r = i % 2 === 0 ? size : inner;
      const angle = (i * Math.PI) / 4 - Math.PI / 2;
      const px = x + r * Math.cos(angle);
      const py = y + r * Math.sin(angle);
      if (i === 0) g.moveTo(px, py);
      else g.lineTo(px, py);
    }
    g.closePath();
    g.fillPath();
    this.ui.push(g);

    this.tweens.add({
      targets: g,
      alpha: 0.65,
      scaleX: 1.12,
      scaleY: 1.12,
      duration: 1200 + Math.random() * 800,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut',
    });
    return g;
  }

  private drawButtonAccents(cx: number, cy: number, btnWidth: number) {
    const g = this.add.graphics();
    const leftX = cx - btnWidth / 2 - 14;
    const rightX = cx + btnWidth / 2 + 14;

    const raysLeft = [
      { dx: -13, dy: -9, color: 0xfbb03b, width: 4 },
      { dx: -16, dy: 0, color: 0xf43f5e, width: 4 },
      { dx: -13, dy: 9, color: 0x8b5cf6, width: 4 },
    ];
    const raysRight = [
      { dx: 13, dy: -9, color: 0xfbb03b, width: 4 },
      { dx: 16, dy: 0, color: 0x8b5cf6, width: 4 },
      { dx: 13, dy: 9, color: 0xf43f5e, width: 4 },
    ];

    const drawRays = (originX: number, originY: number, rays: typeof raysLeft) => {
      rays.forEach((r) => {
        g.lineStyle(r.width, r.color, 0.95);
        g.lineBetween(originX + r.dx * 0.2, originY + r.dy * 0.2, originX + r.dx, originY + r.dy);
      });
    };

    drawRays(leftX, cy, raysLeft);
    drawRays(rightX, cy, raysRight);
    this.ui.push(g);
  }

  private panel(x: number, y: number, width: number, height: number, alpha = 0.95) {
    const panel = this.add.graphics().fillStyle(0xffffff, alpha).fillRoundedRect(x, y, width, height, 34);
    panel.lineStyle(5, 0xffffff, 0.96).strokeRoundedRect(x, y, width, height, 34);
    this.ui.push(panel);
    return panel;
  }

  private button(x: number, y: number, width: number, label: string, fn: () => void, color = COLORS.purple, disabled = false) {
    const shape = this.add.graphics()
      .fillStyle(disabled ? 0xc5c4d1 : color, 1)
      .fillRoundedRect(x - width / 2, y - 28, width, 56, 28);
    this.ui.push(shape);
    const hit = this.add.rectangle(x, y, width, 56, 0xffffff, 0.001)
      .setInteractive({ useHandCursor: !disabled });
    this.ui.push(hit);
    if (!disabled) {
      hit.on('pointerdown', fn);
      hit.on('pointerover', () => shape.setAlpha(0.92));
      hit.on('pointerout', () => shape.setAlpha(1));
    }
    this.text(x, y, label, {
      fontSize: '20px',
      fontStyle: 'bold',
      color: '#fff',
    }).setOrigin(0.5);
  }

  private render() {
    this.ui.forEach((object) => object.destroy());
    this.ui = [];
    this.kidG.clear();
    stopSpeech();
    this.cameras.main.setScroll(0, 0);

    if (this.step === 0) {
      this.renderWelcome();
    } else if (this.step === 1) {
      this.renderSelection();
    } else {
      this.renderTutorial();
    }
  }

  private renderWelcome() {
    // Floating golden sparkles around scene
    this.drawSparkle(50, 95, 16, 0xfbb03b);
    this.drawSparkle(780, 185, 14, 0xfbb03b);
    this.drawSparkle(1050, 155, 16, 0xfbb03b);
    this.drawSparkle(1130, 275, 13, 0xfbb03b);
    this.drawSparkle(1080, 460, 12, 0xfbb03b);

    this.text(80, 82, 'Welcome, guardian\nof the castle!', {
      fontSize: '40px',
      fontStyle: 'bold',
      lineSpacing: -2,
      color: '#16234f',
      wordWrap: { width: 480 },
    });

    this.text(80, 196, 'The castle needs you!', {
      fontSize: '24px',
      fontStyle: 'bold',
      color: '#7253d3',
    });

    this.text(
      80,
      242,
      this.prescribed
        ? 'Your therapist has chosen 3 magical challenges for you.\nThe ogre will also come to test your statue reflexes!'
        : 'Choose 3 magical challenges for your game!\nThe ogre will also come to test your statue reflexes!',
      {
        fontSize: '17px',
        color: '#26335a',
        lineSpacing: 6,
        wordWrap: { width: 480 },
      },
    );

    // 3 Cards: Défi mouvement, Défi précision, Défi statue
    const welcomeCards = [
      { key: 'card_mouvement', name: 'Movement challenge', fill: 0xedf5ff, border: 0xd6e8fa },
      { key: 'card_precision', name: 'Precision challenge', fill: 0xfff0f6, border: 0xfadbe9 },
      { key: 'card_statue', name: 'Statue challenge', fill: 0xecfdf3, border: 0xd2f5e0 },
    ];

    const centers = [150, 305, 460];

    welcomeCards.forEach((cardDef, index) => {
      const x = centers[index];
      const y = 385;
      const cardW = 138;
      const cardH = 120;

      const card = this.add.graphics()
        .fillStyle(cardDef.fill, 0.95)
        .fillRoundedRect(x - cardW / 2, y - cardH / 2, cardW, cardH, 20)
        .lineStyle(1.5, cardDef.border, 0.95)
        .strokeRoundedRect(x - cardW / 2, y - cardH / 2, cardW, cardH, 20);
      this.ui.push(card);

      // Badge on top-left of card
      const badgeX = x - cardW / 2 + 13;
      const badgeY = y - cardH / 2 + 13;
      const badge = this.add.graphics()
        .fillStyle(0x7654d8, 1)
        .fillRoundedRect(badgeX - 10, badgeY - 10, 20, 20, 6);
      this.ui.push(badge);
      this.text(badgeX, badgeY, String(index + 1), {
        fontSize: '11px',
        fontStyle: 'bold',
        color: '#fff',
      }).setOrigin(0.5);

      // Card illustration image
      if (this.textures.exists(cardDef.key)) {
        const img = this.add.image(x, y - 8, cardDef.key)
          .setDisplaySize(66, 66);
        this.ui.push(img);
      }

      // Name
      this.text(x, y + 38, cardDef.name, {
        fontSize: '14px',
        fontStyle: 'bold',
        color: '#16234f',
      }).setOrigin(0.5);
    });

    // Button
    const btnX = 295;
    const btnY = 540;
    const btnW = 300;

    this.button(
      btnX,
      btnY,
      btnW,
      'Discover my 3 challenges  ▶',
      () => {
        this.step = 1;
        this.render();
      },
    );
    this.drawButtonAccents(btnX, btnY, btnW);

    speak(this.prescribed
      ? 'Welcome, guardian of the castle! The castle needs you. Your therapist has chosen 3 magical challenges for you. The ogre will also come to test your statue reflexes!'
      : 'Welcome, guardian of the castle! The castle needs you. Choose 3 magical challenges for your game! The ogre will also come to test your statue reflexes!');
  }

  private toggleChoice(kind: GoKind) {
    const index = this.selected.indexOf(kind);
    if (index >= 0) {
      if (this.selected.length > 1) this.selected.splice(index, 1);
    } else if (this.selected.length < 3) {
      this.selected.push(kind);
    } else {
      this.selected.shift();
      this.selected.push(kind);
    }
    this.render();
  }

  private renderSelection() {
    this.panel(50, 20, 960, 676, 0.96);

    // Sparkle near title
    this.drawSparkle(85, 58, 16, 0xfbb03b);

    this.text(118, 40, 'Choose your 3 magical challenges!', {
      fontSize: '32px',
      fontStyle: 'bold',
      color: '#16234f',
    });

    this.text(118, 80, 'Select the gestures you will perform', {
      fontSize: '17px',
      fontStyle: 'bold',
      color: '#7253d3',
    });

    const count = this.selected.length;
    const isFull = count === 3;

    // Status pill
    const statusBg = this.add.graphics()
      .fillStyle(isFull ? 0xe8f8ee : 0xfef3c7, 1)
      .fillRoundedRect(118, 112, isFull ? 210 : 250, 30, 15)
      .lineStyle(1.5, isFull ? 0x22c55e : 0xf59e0b, 0.8)
      .strokeRoundedRect(118, 112, isFull ? 210 : 250, 30, 15);
    this.ui.push(statusBg);

    this.text(118 + (isFull ? 105 : 125), 127, isFull ? '✓ 3 gestures selected' : `${3 - count} more gesture(s) to choose`, {
      fontSize: '13px',
      fontStyle: 'bold',
      color: isFull ? '#16803c' : '#b45309',
    }).setOrigin(0.5);

    const positions = [
      { x: 210, y: 245 },
      { x: 530, y: 245 },
      { x: 850, y: 245 },
      { x: 210, y: 430 },
      { x: 530, y: 430 },
    ];

    GESTURE_OPTIONS.forEach((option, index) => {
      const { x, y } = positions[index];
      const selected = this.selected.includes(option.kind);

      const card = this.add.graphics()
        .fillStyle(0xffffff, 0.98)
        .fillRoundedRect(x - 145, y - 80, 290, 160, 22)
        .lineStyle(selected ? 3 : 1.5, selected ? 0x22c55e : 0xe2e8f0, 1)
        .strokeRoundedRect(x - 145, y - 80, 290, 160, 22);
      this.ui.push(card);

      const hit = this.add.rectangle(x, y, 290, 160, 0xffffff, 0.001)
        .setInteractive({ useHandCursor: true })
        .on('pointerdown', () => this.toggleChoice(option.kind));
      this.ui.push(hit);

      // Badge top-left: purple square with number
      const numBg = this.add.graphics()
        .fillStyle(0x7654d8, 1)
        .fillRoundedRect(x - 130, y - 68, 24, 24, 7);
      this.ui.push(numBg);
      this.text(x - 118, y - 56, String(index + 1), {
        fontSize: '12px',
        fontStyle: 'bold',
        color: '#fff',
      }).setOrigin(0.5);

      // Checkmark badge top-right if selected
      if (selected) {
        const checkBg = this.add.graphics()
          .fillStyle(0x22c55e, 1)
          .fillCircle(x + 124, y - 56, 12);
        this.ui.push(checkBg);
        this.text(x + 124, y - 56, '✓', {
          fontSize: '13px',
          fontStyle: 'bold',
          color: '#fff',
        }).setOrigin(0.5);
      }

      // Card illustration image
      if (this.textures.exists(option.imageKey)) {
        const img = this.add.image(x, y - 18, option.imageKey)
          .setDisplaySize(72, 72);
        this.ui.push(img);
      } else {
        this.text(x, y - 24, option.emoji, { fontSize: '38px' }).setOrigin(0.5);
      }

      // Name
      this.text(x, y + 26, option.name, { fontSize: '17px', fontStyle: 'bold', color: '#16234f' }).setOrigin(0.5);
      // Subtitle
      this.text(x, y + 46, option.action, { fontSize: '13px', color: '#64748b' }).setOrigin(0.5);

      // Bottom pill
      const pillW = selected ? 100 : 92;
      const pillBg = this.add.graphics()
        .fillStyle(selected ? 0xe8f8ee : 0xf1f0f7, 1)
        .fillRoundedRect(x - pillW / 2, y + 57, pillW, 22, 11);
      this.ui.push(pillBg);
      this.text(x, y + 68, selected ? '✓ CHOSEN' : '+ Add', {
        fontSize: '11px',
        fontStyle: 'bold',
        color: selected ? '#16803c' : '#64748b',
      }).setOrigin(0.5);
    });

    // Card 6: L'ogre statue
    const ox = 850, oy = 430;
    const ogreCard = this.add.graphics()
      .fillStyle(0xfff1f2, 0.98)
      .fillRoundedRect(ox - 145, oy - 80, 290, 160, 22)
      .lineStyle(1.5, 0xfecdd3, 1)
      .strokeRoundedRect(ox - 145, oy - 80, 290, 160, 22);
    this.ui.push(ogreCard);

    // Badge 6 top-left
    const ogreNumBg = this.add.graphics()
      .fillStyle(0x7654d8, 1)
      .fillRoundedRect(ox - 130, oy - 68, 24, 24, 7);
    this.ui.push(ogreNumBg);
    this.text(ox - 118, oy - 56, '6', {
      fontSize: '12px',
      fontStyle: 'bold',
      color: '#fff',
    }).setOrigin(0.5);

    // Badge OBLIGATOIRE top-right
    const reqBg = this.add.graphics()
      .fillStyle(0xe11d48, 1)
      .fillRoundedRect(ox + 40, oy - 68, 92, 22, 11);
    this.ui.push(reqBg);
    this.text(ox + 86, oy - 57, '🔒 MANDATORY', {
      fontSize: '10px',
      fontStyle: 'bold',
      color: '#fff',
    }).setOrigin(0.5);

    // Ogre illustration image
    if (this.textures.exists('sel_ogre')) {
      const ogreImg = this.add.image(ox, oy - 18, 'sel_ogre')
        .setDisplaySize(72, 72);
      this.ui.push(ogreImg);
    } else {
      this.text(ox, oy - 24, '🐻', { fontSize: '38px' }).setOrigin(0.5);
    }

    this.text(ox, oy + 26, 'The statue ogre', { fontSize: '17px', fontStyle: 'bold', color: '#9f1239' }).setOrigin(0.5);
    this.text(ox, oy + 46, 'Don\'t move!', { fontSize: '13px', color: '#64748b' }).setOrigin(0.5);

    // Bottom buttons
    this.button(210, 615, 190, '◀  Home', () => {
      this.step = 0;
      this.render();
    }, 0x8c83b5);
    this.drawButtonAccents(210, 615, 190);

    this.button(690, 615, 360, 'Confirm my 3 gestures  ▶', () => {
      if (this.selected.length === 3) {
        this.step = 2;
        this.render();
      }
    }, COLORS.purple, this.selected.length !== 3);
    this.drawButtonAccents(690, 615, 360);
  }

  private getTutorialSlides(): TutorialSlide[] {
    const slides: TutorialSlide[] = [];
    this.selected.forEach((kind) => {
      const definition = GESTURE_OPTIONS.find((option) => option.kind === kind);
      if (definition) {
        // Each character image is used ONCE to indicate which hand/gesture to make
        let imageKey: string | undefined;
        if (kind === 'fairy_r') imageKey = 'tut_boy_finger';       // boy pointing right
        else if (kind === 'fairy_l') imageKey = 'tut_girl_pink';   // girl pointing left/up
        else if (kind === 'star') imageKey = 'tut_boy_green';      // boy both arms up
        else if (kind === 'crown') imageKey = 'tut_boy_purple';    // purple hoodie boy = couronne
        else if (kind === 'dragon') imageKey = 'tut_chibi_crouch'; // crouching girl = baisse-toi

        // Mascot badge: the creature the player will need to react to
        const badgeKey = definition.imageKey; // e.g. sel_fairy_r, sel_star…

        slides.push({
          title: `${definition.name} ${definition.emoji}`,
          text: definition.desc,
          imageKey,
          badgeKey,
        });
      }
    });

    // Ogre slide – keep red girl as "freeze" indicator
    slides.push({
      title: 'The ogre 👹',
      text: 'When the ogre appears, don\'t move at all!\n\nStay like a statue 🗿 until it disappears.',
      imageKey: 'tut_girl_red',
    });

    // "Avant de jouer" – no character, centered text only
    slides.push({
      title: 'Before playing 📋',
      text: 'Stand UP straight in the guide frame.\n\nStand two steps away from the screen, fully visible, with good lighting.',
    });

    // "On s’entraîne" – no character, centered text only
    slides.push({
      title: 'Let\'s practice first! 🎮',
      text: '4 practice rounds (your 3 gestures + the ogre), then the real game to defend the castle.\n\nReady, guardian?',
    });

    return slides;
  }

  private renderTutorial() {
    const slides = this.getTutorialSlides();
    const index = this.step - 2;
    const slide = slides[index];
    const last = index === slides.length - 1;
    this.panel(60, 24, 1160, 672, 0.96);

    if (slide.imageKey && this.textures.exists(slide.imageKey)) {
      // Layout: character (left) | text (centre) | creature badge (right)
      const hasBadge = slide.badgeKey && this.textures.exists(slide.badgeKey);

      // ── Left: character illustration doing the gesture ──
      const charImg = this.add.image(200, 360, slide.imageKey)
        .setDisplaySize(300, 300);
      this.ui.push(charImg);
      this.tweens.add({
        targets: charImg,
        y: 350,
        duration: 1800,
        yoyo: true,
        repeat: -1,
        ease: 'Sine.easeInOut',
      });

      // ── Centre: instruction text ──
      const textX = hasBadge ? 600 : 700;
      this.text(textX, 350, slide.text, {
        fontSize: '24px',
        color: '#1f2937',
        align: 'center',
        lineSpacing: 12,
        wordWrap: { width: hasBadge ? 370 : 560 },
      }).setOrigin(0.5);

      // ── Right: creature mascot badge ──
      if (hasBadge) {
        const badgeImg = this.add.image(1070, 340, slide.badgeKey!)
          .setDisplaySize(260, 260);
        this.ui.push(badgeImg);
        this.tweens.add({
          targets: badgeImg,
          y: 330,
          duration: 2200,
          yoyo: true,
          repeat: -1,
          ease: 'Sine.easeInOut',
        });

        // Small label under the badge
        this.text(1070, 490, 'When you see this →', {
          fontSize: '15px',
          color: '#7654d8',
          fontStyle: 'italic',
        }).setOrigin(0.5);
      }
    } else {
      this.text(640, 350, slide.text, {
        fontSize: '26px',
        color: '#1f2937',
        align: 'center',
        lineSpacing: 12,
        wordWrap: { width: 820 },
      }).setOrigin(0.5);
    }

    // Step pagination dots
    this.text(
      640,
      570,
      slides.map((_, slideIndex) => (slideIndex === index ? '●' : '○')).join('   '),
      { fontSize: '22px', color: '#7654d8' },
    ).setOrigin(0.5);

    // Navigation buttons
    this.button(210, 620, 200, '◀  Previous', () => {
      this.step = this.step === 2 ? 1 : this.step - 1;
      this.render();
    }, 0x8c83b5);
    this.drawButtonAccents(210, 620, 200);

    if (last) {
      this.button(1010, 620, 380, 'Start practice  ▶', () => {
        this.scene.start('main', { kinds: this.selected });
      });
      this.drawButtonAccents(1010, 620, 380);
    } else {
      this.button(1030, 620, 220, 'Next  ▶', () => {
        this.step++;
        this.render();
      });
      this.drawButtonAccents(1030, 620, 220);
    }
    speak(`${slide.title}. ${slide.text}`, 0.85);
  }
}
