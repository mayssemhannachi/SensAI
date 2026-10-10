import Phaser from 'phaser';
import { drawBackdrop, drawKid, type KidPose } from './castle';
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
}

const GESTURE_OPTIONS: GestureDef[] = [
  {
    kind: 'fairy_r',
    emoji: '🔵🧚',
    name: 'Fée bleue',
    action: 'Bras DROIT',
    desc: 'Lève vite ton BRAS DROIT !\n\nComme dans un miroir : ton bras droit est à droite sur l’écran.',
    kid: 'right',
  },
  {
    kind: 'fairy_l',
    emoji: '💗🧚',
    name: 'Fée rose',
    action: 'Bras GAUCHE',
    desc: 'Lève vite ton BRAS GAUCHE !\n\nTon bras gauche est à gauche sur l’écran.',
    kid: 'left',
  },
  {
    kind: 'star',
    emoji: '⭐',
    name: 'Étoile filante',
    action: 'Les 2 bras',
    desc: 'Lève les DEUX bras bien haut, comme une grande étoile !',
    kid: 'both',
  },
  {
    kind: 'crown',
    emoji: '👑',
    name: 'Couronne',
    action: 'Main sur la tête',
    desc: 'Mets vite une main sur ta tête pour porter la couronne !',
    kid: 'head',
  },
  {
    kind: 'dragon',
    emoji: '🐉',
    name: 'Dragon',
    action: 'Baisse-toi !',
    desc: 'Baisse-toi vite (accroupi) pour te cacher du dragon, puis relève-toi !',
    kid: 'duck',
  },
];

interface TutorialSlide {
  title: string;
  text: string;
  kid?: KidPose;
}

export class IntroScene extends Phaser.Scene {
  private step = 0; // 0 = accueil, 1 = sélection des 3 gestes, 2+ = tutoriel dynamique
  // SensAI : si l'ergothérapeute a prescrit les 3 défis, ils sont imposés (pas d'écran de choix)
  private prescribed = PRESCRIPTION.kinds as GoKind[] | null;
  private selected: GoKind[] = this.prescribed ? [...this.prescribed] : ['fairy_r', 'fairy_l', 'star']; // 3 par défaut
  private ui: Phaser.GameObjects.GameObject[] = [];
  private kidG!: Phaser.GameObjects.Graphics;

  constructor() {
    super('intro');
  }

  create() {
    drawBackdrop(this, true);
    this.kidG = this.add.graphics();
    this.render();
  }

  private btn(x: number, y: number, label: string, fn: () => void, color = '#6c4ad6', disabled = false) {
    const t = this.add
      .text(x, y, label, {
        fontSize: '28px',
        color: disabled ? '#888' : '#fff',
        backgroundColor: disabled ? '#3a3d52' : color,
        padding: { x: 20, y: 10 },
      })
      .setOrigin(0.5);
    if (!disabled) {
      t.setInteractive({ useHandCursor: true }).on('pointerdown', fn);
    }
    this.ui.push(t);
    return t;
  }

  private render() {
    this.ui.forEach((o) => o.destroy());
    this.ui = [];
    this.kidG.clear();
    stopSpeech();

    if (this.step === 0) {
      this.renderWelcome();
    } else if (this.step === 1) {
      this.renderSelection();
    } else {
      this.renderTutorial();
    }
  }

  private renderWelcome() {
    const w = this.scale.width;
    this.ui.push(
      this.add
        .text(w / 2, 100, 'Bienvenue, gardien du château ! 🏰', {
          fontSize: '44px',
          color: '#1d2b53',
          fontStyle: 'bold',
          stroke: '#fff',
          strokeThickness: 7,
          align: 'center',
        })
        .setOrigin(0.5)
    );

    this.ui.push(
      this.add
        .text(
          w / 2,
          320,
          this.prescribed
            ? 'Le château a besoin de toi !\n\nTon thérapeute a choisi pour toi 3 défis magiques.\n\nL’ogre 👹 viendra aussi tester tes réflexes de statue !\n\nPrêt à découvrir tes défis ?'
            : 'Le château a besoin de toi !\n\nPour que le jeu soit facile et amusant à mémoriser,\ntu vas choisir 3 défis magiques.\n\nL’ogre 👹 viendra aussi tester tes réflexes de statue !\n\nPrêt à composer ta partie ?',
          {
            fontSize: '30px',
            color: '#1d2b53',
            align: 'center',
            backgroundColor: '#ffffffdd',
            padding: { x: 26, y: 18 },
            lineSpacing: 10,
            wordWrap: { width: 820 },
          }
        )
        .setOrigin(0.5)
    );

    this.btn(w / 2, 570, this.prescribed ? '✨ Découvrir mes 3 défis ▶' : '✨ Choisir mes 3 gestes ▶', () => {
      this.step = this.prescribed ? 2 : 1;
      this.render();
    }, '#2e9e5b');

    speak(this.prescribed
      ? 'Bienvenue, gardien du château ! Le château a besoin de toi. Ton thérapeute a choisi 3 défis magiques pour toi.'
      : 'Bienvenue, gardien du château ! Le château a besoin de toi. Tu vas choisir 3 défis magiques.');
  }

  private toggleChoice(k: GoKind) {
    const idx = this.selected.indexOf(k);
    if (idx >= 0) {
      if (this.selected.length > 1) {
        this.selected.splice(idx, 1);
      }
    } else {
      if (this.selected.length < 3) {
        this.selected.push(k);
      } else {
        // Remplace le premier sélectionné si déjà 3 pour garder l'interaction fluide
        this.selected.shift();
        this.selected.push(k);
      }
    }
    this.render();
  }

  private renderSelection() {
    const w = this.scale.width;
    this.ui.push(
      this.add
        .text(w / 2, 55, 'Choisis 3 défis magiques ! ✨', {
          fontSize: '40px',
          color: '#1d2b53',
          fontStyle: 'bold',
          stroke: '#fff',
          strokeThickness: 6,
          align: 'center',
        })
        .setOrigin(0.5)
    );

    const count = this.selected.length;
    const statusTxt = count === 3 ? '✓ 3 gestes sélectionnés !' : `Sélectionne encore ${3 - count} geste(s)...`;
    const statusColor = count === 3 ? '#1e7b34' : '#b25e00';

    this.ui.push(
      this.add
        .text(w / 2, 105, statusTxt, {
          fontSize: '24px',
          color: statusColor,
          fontStyle: 'bold',
          backgroundColor: '#ffffffcc',
          padding: { x: 14, y: 4 },
        })
        .setOrigin(0.5)
    );

    // Grille 2 x 3 : 5 cartes au choix + 1 carte Ogre obligatoire
    const positions = [
      { x: 190, y: 220 },
      { x: 480, y: 220 },
      { x: 770, y: 220 },
      { x: 190, y: 410 },
      { x: 480, y: 410 },
    ];

    GESTURE_OPTIONS.forEach((opt, idx) => {
      const pos = positions[idx];
      const isSel = this.selected.includes(opt.kind);
      const bg = this.add
        .rectangle(pos.x, pos.y, 250, 150, isSel ? 0xd4edda : 0xffffff, 0.95)
        .setStrokeStyle(isSel ? 4 : 2, isSel ? 0x28a745 : 0xcccccc)
        .setInteractive({ useHandCursor: true })
        .on('pointerdown', () => this.toggleChoice(opt.kind));
      this.ui.push(bg);

      const emoji = this.add.text(pos.x, pos.y - 38, opt.emoji, { fontSize: '42px' }).setOrigin(0.5);
      const name = this.add
        .text(pos.x, pos.y + 6, opt.name, {
          fontSize: '22px',
          color: '#1d2b53',
          fontStyle: 'bold',
        })
        .setOrigin(0.5);
      const action = this.add
        .text(pos.x, pos.y + 34, opt.action, {
          fontSize: '18px',
          color: '#555566',
        })
        .setOrigin(0.5);

      const badge = this.add
        .text(pos.x, pos.y + 58, isSel ? '✓ CHOISI' : '+ Cliquer', {
          fontSize: '14px',
          color: isSel ? '#155724' : '#666',
          fontStyle: 'bold',
          backgroundColor: isSel ? '#b8e2c0' : '#e9ecef',
          padding: { x: 8, y: 2 },
        })
        .setOrigin(0.5);

      this.ui.push(emoji, name, action, badge);
    });

    // 6ème carte : L'ogre (Obligatoire)
    const ogrePos = { x: 770, y: 410 };
    const ogreBg = this.add
      .rectangle(ogrePos.x, ogrePos.y, 250, 150, 0xfce8e6, 0.95)
      .setStrokeStyle(3, 0xd93829);
    this.ui.push(ogreBg);

    const ogreEmoji = this.add.text(ogrePos.x, ogrePos.y - 38, '👹', { fontSize: '42px' }).setOrigin(0.5);
    const ogreName = this.add
      .text(ogrePos.x, ogrePos.y + 6, 'L’ogre statue', {
        fontSize: '22px',
        color: '#7b1113',
        fontStyle: 'bold',
      })
      .setOrigin(0.5);
    const ogreAction = this.add
      .text(ogrePos.x, ogrePos.y + 34, 'Ne bouge plus !', {
        fontSize: '18px',
        color: '#555566',
      })
      .setOrigin(0.5);
    const ogreBadge = this.add
      .text(ogrePos.x, ogrePos.y + 58, '🔒 OBLIGATOIRE', {
        fontSize: '14px',
        color: '#fff',
        fontStyle: 'bold',
        backgroundColor: '#d93829',
        padding: { x: 8, y: 2 },
      })
      .setOrigin(0.5);
    this.ui.push(ogreEmoji, ogreName, ogreAction, ogreBadge);

    // Barre d'action
    this.btn(140, 660, '◀ Accueil', () => {
      this.step = 0;
      this.render();
    }, '#8a8fa8');

    const canContinue = this.selected.length === 3;
    this.btn(
      780,
      660,
      'Valider mes 3 gestes ▶',
      () => {
        if (canContinue) {
          this.step = 2; // commence les explications des 3 gestes
          this.render();
        }
      },
      '#2e9e5b',
      !canContinue
    );
  }

  private getTutorialSlides(): TutorialSlide[] {
    const slides: TutorialSlide[] = [];

    // Slides pour chacun des 3 gestes choisis
    this.selected.forEach((kind) => {
      const def = GESTURE_OPTIONS.find((g) => g.kind === kind);
      if (def) {
        slides.push({
          title: `${def.name} ${def.emoji}`,
          text: `${def.desc}\n\n👉 Geste : ${def.action}`,
          kid: def.kid,
        });
      }
    });

    // Slide Ogre (obligatoire)
    slides.push({
      title: 'L’ogre 👹',
      text: 'Quand l’ogre apparaît, ne bouge plus du tout !\n\nReste comme une statue 🗿 jusqu’à ce qu’il disparaisse.',
      kid: 'still',
    });

    // Slide recommandations
    slides.push({
      title: 'Avant de jouer',
      text: 'Zone de départ : Reste bien DEBOUT dans le cadre guide.\n\nPlace-toi à deux pas de l’écran, bien visible en entier, avec une bonne lumière.',
      kid: 'still',
    });

    // Slide finale de l'entraînement
    slides.push({
      title: 'On s’entraîne d’abord !',
      text: '4 essais pour de faux (tes 3 gestes + l’ogre),\npuis la vraie partie pour défendre le château.\n\nPrêt, gardien ?',
    });

    return slides;
  }

  private renderTutorial() {
    const slides = this.getTutorialSlides();
    const tutIdx = this.step - 2;
    const s = slides[tutIdx];
    const w = this.scale.width;
    const last = tutIdx === slides.length - 1;

    this.ui.push(
      this.add
        .text(w / 2, 70, s.title, {
          fontSize: '44px',
          color: '#1d2b53',
          fontStyle: 'bold',
          stroke: '#fff',
          strokeThickness: 7,
          align: 'center',
        })
        .setOrigin(0.5)
    );

    this.ui.push(
      this.add
        .text(s.kid ? 600 : w / 2, s.kid ? 300 : 250, s.text, {
          fontSize: '30px',
          color: '#1d2b53',
          align: 'center',
          backgroundColor: '#ffffffdd',
          padding: { x: 22, y: 16 },
          lineSpacing: 8,
          wordWrap: { width: s.kid ? 560 : 800 },
        })
        .setOrigin(0.5)
    );

    if (s.kid) drawKid(this.kidG, 170, 440, 1.5, s.kid);

    // Indicateur de pagination
    this.ui.push(
      this.add
        .text(
          w / 2,
          700,
          slides.map((_, j) => (j === tutIdx ? '●' : '○')).join(' '),
          { fontSize: '26px', color: '#fff', stroke: '#000', strokeThickness: 4 }
        )
        .setOrigin(0.5)
    );

    // Boutons de navigation
    this.btn(140, 690, '◀ Précédent', () => {
      this.step = this.prescribed && this.step === 2 ? 0 : this.step - 1;
      this.render();
    }, '#8a8fa8');

    if (last) {
      this.btn(
        740,
        690,
        '▶ Commencer l’entraînement',
        () => this.scene.start('main', { kinds: this.selected }),
        '#2e9e5b'
      );
    } else {
      this.btn(820, 690, 'Suivant ▶', () => {
        this.step++;
        this.render();
      });
    }

    // Lire le titre + texte de la slide à voix haute
    speak(`${s.title}. ${s.text}`, 0.85);
  }
}