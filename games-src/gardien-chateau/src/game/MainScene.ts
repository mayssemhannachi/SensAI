import Phaser from 'phaser';
import { Tracker } from '../pose/tracker';
import { classifyGesture, motionSpeed, thresholds, type Gesture, type Pose, type Posture } from '../core/gestures';
import { summarize, type Kind, type TrialResult } from '../core/metrics';
import { buildTrials, Staircase } from '../core/engine';
import { drawBackdrop, drawInitialZone } from './castle';
import { speak, stopSpeech } from './speech';
import { PRESCRIPTION, onStopRequest, toPlatform } from '../platform';

type Phase = 'load' | 'calib' | 'gap' | 'stim' | 'fb' | 'pause' | 'result';
type Go = Exclude<Kind, 'enemy'>;
const HOLD_MS = 250;
const CX = 780, CY = 230; // place du personnage : en haut à droite, la caméra reste visible

/** voice = consigne orale courte et claire pour l'enfant */
const INFO: Record<Go, { e: string; voice: string; g: Gesture }> = {
  fairy_r: {
    e: '🔵🧚',
    voice: 'Fée bleue ! Bras droit !',
    g: 'right',
  },
  fairy_l: {
    e: '💗🧚',
    voice: 'Fée rose ! Bras gauche !',
    g: 'left',
  },
  star: {
    e: '⭐',
    voice: "Étoile ! Les deux bras !",
    g: 'both',
  },
  crown: {
    e: '👑',
    voice: 'Couronne ! Main sur la tête !',
    g: 'head',
  },
  dragon: {
    e: '🐉',
    voice: 'Dragon ! Baisse-toi !',
    g: 'duck',
  },
};
const ALL: Kind[] = ['fairy_r', 'fairy_l', 'star', 'crown', 'dragon'];

export class MainScene extends Phaser.Scene {
  private tracker = new Tracker();
  private video!: HTMLVideoElement;
  private emo!: Phaser.GameObjects.Text;
  private msg!: Phaser.GameObjects.Text;
  private tag!: Phaser.GameObjects.Text;
  private starTxt!: Phaser.GameObjects.Text;
  private glow!: Phaser.GameObjects.Arc;
  private bar!: Phaser.GameObjects.Rectangle;
  private bob?: Phaser.Tweens.Tween;
  private phase: Phase = 'load';
  private pose: Pose | null = null;
  private prevPose: Pose | null = null;
  private prevT = 0;
  private lastVid = -1;
  private speed = 0;
  private thr = { still: 0.1, move: 0.4 };
  private base: { noseY: number } | undefined;
  private noise: number[] = [];
  private noseS: number[] = [];
  private calibEnd = 0;
  // SensAI : nombre d'essais et proportion de défis réglés par l'ergothérapeute
  private cfg = { n: PRESCRIPTION.trials, goRatio: PRESCRIPTION.goRatio, kinds: ALL };
  private startedAt = 0;
  private sent = false;
  private trials: Kind[] = [];
  private idx = 0;
  private practice = true;
  private stars = 0;
  private results: TrialResult[] = [];
  private fairy = new Staircase(2000, 1200, 3000, 150, 200, true);
  private enemy = new Staircase(2000, 1500, 3500, 250, 250, false);
  private kind: Kind = 'enemy';
  private until = 0;
  private t0 = 0;
  private hold: number | null = null;
  private bad: number | null = null;
  private moveS: number | null = null;
  private stillS: number | null = null;
  private stopMs: number | null = null;
  private moving0 = false;
  private sum = 0;
  private cnt = 0;
  private audioPlaying = false;
  private audioEndAt: number | null = null;
  private zoneG!: Phaser.GameObjects.Graphics;
  private inZone = false;
  private inZoneSince = 0;

  constructor() { super('main'); }

  init(data?: { kinds?: Kind[] }) {
    if (data?.kinds && data.kinds.length === 3) {
      this.cfg.kinds = data.kinds;
    }
  }

  create() {
    drawBackdrop(this);
    const w = this.scale.width;
    this.bar = this.add.rectangle(0, 0, 0, 10, 0xffd23f).setOrigin(0, 0);
    this.glow = this.add.circle(CX, CY, 110, 0xffffff, 0.4).setVisible(false);
    this.emo = this.add.text(CX, CY, '', { fontSize: '150px' }).setOrigin(0.5);
    this.msg = this.add.text(w / 2, 610, '', {
      fontSize: '38px', color: '#fff', backgroundColor: '#1d2b53dd', padding: { x: 20, y: 12 }, align: 'center', wordWrap: { width: 860 },
    }).setOrigin(0.5).setVisible(false);
    this.tag = this.add.text(24, 24, '', { fontSize: '28px', color: '#fff', backgroundColor: '#6c4ad6', padding: { x: 12, y: 6 } }).setVisible(false);
    this.starTxt = this.add.text(w - 24, 24, '', { fontSize: '40px', color: '#fff', stroke: '#000', strokeThickness: 5 }).setOrigin(1, 0);

    // Zone guide caméra (silhouette debout)
    this.zoneG = this.add.graphics();

    void this.startCamera();
  }

  private isPoseInInitialZone(p: Pose): boolean {
    if (!p || p.length < 25) return false;
    const nose = p[0], lSh = p[11], rSh = p[12];
    const vis = (pt?: { visibility?: number }) => (pt?.visibility ?? 1) > 0.45;
    if (!vis(nose) || !vis(lSh) || !vis(rSh)) return false;
    const midX = (lSh.x + rSh.x) / 2;
    if (midX < 0.22 || midX > 0.78) return false;
    if (nose.y < 0.08 || nose.y > 0.6) return false;
    return true;
  }

  private say(s: string) {
    this.msg.setText(s).setVisible(s !== '');
    if (s) speak(s); else stopSpeech();
  }
  private setTag(s: string) { this.tag.setText(s).setVisible(s !== ''); }

  /** Affiche un personnage avec une petite animation (apparition + flottement). */
  private show(e: string) {
    this.bob?.stop();
    this.tweens.killTweensOf([this.emo, this.glow]);
    this.emo.setText(e).setY(CY).setScale(1);
    this.glow.setVisible(e !== '').setScale(1);
    if (!e) return;
    this.tweens.add({ targets: [this.emo, this.glow], scale: { from: 0, to: 1 }, duration: 320, ease: 'Back.Out' });
    this.bob = this.tweens.add({ targets: this.emo, y: CY - 16, yoyo: true, repeat: -1, duration: 500, delay: 320, ease: 'Sine.InOut' });
  }

  private burst(emoji: string, n = 14) {
    for (let i = 0; i < n; i++) {
      const t = this.add.text(CX, CY, emoji, { fontSize: '36px' }).setOrigin(0.5);
      const a = Math.random() * Math.PI * 2, d = 90 + Math.random() * 110;
      this.tweens.add({ targets: t, x: CX + Math.cos(a) * d, y: CY + Math.sin(a) * d, alpha: 0, scale: 0.4, duration: 700, onComplete: () => t.destroy() });
    }
  }

  private async startCamera() {
    this.show('🏰');
    this.say('Chargement du jeu…');
    try {
      await this.tracker.init();
      this.video = document.getElementById('cam') as HTMLVideoElement;
      this.video.srcObject = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480, facingMode: 'user' } });
      await this.video.play();
    } catch (e) {
      this.say('Caméra ou modèle indisponible :\n' + (e as Error).message);
      return;
    }
    this.show('🗿');
    this.phase = 'calib';
    // SensAI : la séance commence, la page peut demander l'arrêt (« J'ai mal / Stop »)
    this.startedAt = Date.now();
    toPlatform({ type: 'started', input: 'camera' });
    onStopRequest(() => this.stopEarly());
    this.inZoneSince = 0;
    this.noise = [];
    this.noseS = [];
    drawInitialZone(this.zoneG, this.scale.width / 2, 380, 'standing', false);
    this.say('Place-toi debout dans le cadre guide…');
  }

  update() {
    if (this.phase === 'load' || this.phase === 'result') return;
    const now = performance.now();
    if (this.video.currentTime !== this.lastVid) {
      this.lastVid = this.video.currentTime;
      const p = this.tracker.detect(this.video, now);
      if (p && this.prevPose) this.speed = motionSpeed(this.prevPose, p, (now - this.prevT) / 1000);
      if (p) { this.prevPose = p; this.prevT = now; }
      this.pose = p;
    }
    this.step(now, classifyGesture(this.pose, this.base, 'standing'));
  }

  private step(now: number, g: Gesture) {
    switch (this.phase) {
      case 'calib': {
        const inZone = this.pose ? this.isPoseInInitialZone(this.pose) : false;
        if (inZone !== this.inZone) {
          this.inZone = inZone;
          drawInitialZone(this.zoneG, this.scale.width / 2, 380, 'standing', inZone);
        }

        if (!inZone) {
          this.inZoneSince = 0;
          this.noise = [];
          this.noseS = [];
        } else {
          if (!this.inZoneSince) {
            this.inZoneSince = now;
            this.say('Parfait ! Reste immobile comme une statue…');
          }
          this.noise.push(this.speed);
          if (this.pose) this.noseS.push(this.pose[0].y);

          // Calibrer pendant 1.8s d'immobilité stabilisée dans la zone
          if (now - this.inZoneSince >= 1800) {
            this.zoneG.clear();
            this.thr = thresholds(this.noise);
            if (this.noseS.length) {
              this.base = { noseY: this.noseS.reduce((a, b) => a + b, 0) / this.noseS.length };
            }
            this.startPlay();
          }
        }
        break;
      }
      case 'gap':
        // Enchaînement direct et fluide : ne bloque plus sur "Bras le long du corps"
        if (now >= this.until) this.begin(now);
        break;
      case 'stim': this.stim(now, g); break;
      case 'fb': if (now >= this.until) this.next(now); break;
      case 'pause': if (now >= this.until) this.startReal(now); break;
    }
  }

  private startPlay() {
    this.practice = true;
    this.trials = [...this.cfg.kinds, 'enemy'];
    this.idx = 0;
    this.setTag('ENTRAÎNEMENT');
    this.show('🏰');
    this.say('Prêt ?\n4 essais pour tester tes gestes !');
    this.phase = 'gap';
    this.until = performance.now() + 3500;
  }

  private endPractice(now: number) {
    this.show('🎉');
    this.say('Bravo ! L’entraînement est fini.\nMaintenant, la vraie partie !');
    this.phase = 'pause';
    this.until = now + 3500;
  }

  private startReal(now: number) {
    this.practice = false;
    this.setTag('');
    this.trials = buildTrials(this.cfg.n, this.cfg.goRatio, this.cfg.kinds);
    this.idx = 0;
    this.results = [];
    this.stars = 0;
    this.bar.width = 0;
    this.starTxt.setText('⭐ 0');
    this.show('🏰');
    this.say('Protège le château !');
    this.phase = 'gap';
    this.until = now + 2000;
  }

  private begin(now: number) {
    this.kind = this.trials[this.idx];
    this.t0 = now;
    this.hold = this.bad = this.moveS = this.stillS = this.stopMs = null;
    this.moving0 = this.speed > this.thr.still;
    this.sum = 0; this.cnt = 0;
    this.phase = 'stim';
    this.audioPlaying = true;
    this.audioEndAt = null;

    // Pas d'écriture pendant les défis du jeu
    this.msg.setVisible(false);

    // Tant que le son parle, on ne déclenche pas le retard (timeout).
    // On met un délai temporaire allongé le temps de la consigne orale.
    const trialDuration = this.kind === 'enemy' ? this.enemy.value : this.fairy.value;
    this.until = now + trialDuration + 6000;

    const voice = this.kind === 'enemy' ? 'Ogre ! Ne bouge plus !' : INFO[this.kind as Go].voice;
    const emoji = this.kind === 'enemy' ? '👹' : INFO[this.kind as Go].e;
    this.show(emoji);

    // Dès que le son termine, on commence à compter le temps pour retard !
    speak(voice, () => {
      if (this.phase === 'stim' && this.audioPlaying) {
        this.audioPlaying = false;
        const audioNow = performance.now();
        this.audioEndAt = audioNow;
        this.until = audioNow + (this.kind === 'enemy' ? this.enemy.value : this.fairy.value);
      }
    });
  }

  private stim(now: number, g: Gesture) {
    const dt = now - this.t0;

    // --- OGRE (No-Go / Statue) ---
    if (this.kind === 'enemy') {
      this.sum += this.speed; this.cnt++;
      if (this.stopMs === null && this.moving0) {
        if (this.speed <= this.thr.still) {
          this.stillS ??= now;
          if (now - this.stillS >= 200) this.stopMs = this.stillS - this.t0;
        } else this.stillS = null;
      }
      // S'il bouge (même pendant la consigne vocale) : repéré immédiatement !
      const isMoving = this.speed > this.thr.move || (g !== 'neutral' && g !== 'unknown');
      if (isMoving) {
        this.moveS ??= now;
        if (now - this.moveS >= 100) return this.finish(now, false);
      } else {
        this.moveS = null;
      }

      // Réussite : le son est terminé ET le temps d'immobilité complet est respecté
      if (!this.audioPlaying && now >= this.until) this.finish(now, true);
      return;
    }

    // --- FÉES ET DÉFIS (Go) ---
    const target = INFO[this.kind as Go].g;
    const good = g === target;
    const wrong = !good && g !== 'neutral' && g !== 'unknown';

    // Si l'enfant est habitué au jeu, il n'attend pas que le son termine :
    // son geste est validé immédiatement !
    if (dt > 250 && good) {
      this.hold ??= now;
      if (now - this.hold >= HOLD_MS) {
        // Temps de réaction : mesuré depuis la fin du son s'il a attendu,
        // ou depuis l'apparition du personnage s'il a réagi pendant le son.
        const rt = (this.audioEndAt && this.hold >= this.audioEndAt)
          ? Math.round(this.hold - this.audioEndAt)
          : Math.round(this.hold - this.t0);
        return this.finish(now, true, Math.max(50, rt));
      }
    } else {
      this.hold = null;
    }

    if (dt > 250 && wrong) {
      this.bad ??= now;
      if (now - this.bad >= HOLD_MS) return this.finish(now, false, undefined, true);
    } else {
      this.bad = null;
    }

    // Le retard n'est compté qu'une fois le son terminé :
    if (!this.audioPlaying && now >= this.until) {
      this.finish(now, false);
    }
  }

  private finish(now: number, ok: boolean, rtMs?: number, wrongArm?: boolean) {
    this.audioPlaying = false;
    stopSpeech(); // Coupe immédiatement la voix si l'enfant a réagi avant la fin du son

    const r: TrialResult = { kind: this.kind, ok, rtMs, wrongArm };
    if (this.kind === 'enemy') {
      r.stopMs = this.stopMs;
      r.agitation = this.cnt ? this.sum / this.cnt / this.thr.move : 0;
      if (!this.practice) this.enemy.update(ok);
    } else if (!this.practice) this.fairy.update(ok);
    if (!this.practice) {
      this.results.push(r);
      if (ok) {
        this.starTxt.setText('⭐ ' + ++this.stars);
        this.tweens.add({ targets: this.starTxt, scale: { from: 1.5, to: 1 }, duration: 250 });
      }
    }

    // Feedback visuel uniquement par emoji et effets (pas d'écriture invasive)
    this.show(ok ? '✨' : wrongArm ? '🔄' : this.kind === 'enemy' ? '😬' : '💤');
    if (ok) this.burst('✨');
    else if (this.kind === 'enemy') {
      this.cameras.main.shake(250, 0.012);
      this.cameras.main.flash(200, 255, 70, 70);
    }

    this.msg.setVisible(false);

    // Retours oraux courts
    const isEnemy = this.kind === 'enemy';
    if (ok) {
      const praise = ['Bravo !', 'Super !', 'Génial !', 'Bien joué !'];
      speak(isEnemy ? 'Bien joué, statue !' : praise[Math.floor(Math.random() * praise.length)]);
    } else if (wrongArm) {
      speak('Pas le bon bras !');
    } else if (isEnemy) {
      speak('L’ogre t’a vu !');
    } else {
      speak('Trop lent ! Plus vite !');
    }

    this.phase = 'fb';
    this.until = now + 650;
  }

  private next(now: number) {
    this.bar.width = (this.scale.width * (this.idx + 1)) / this.trials.length;
    if (!this.practice) toPlatform({ type: 'progress', reps: this.idx + 1, target: this.trials.length });
    if (++this.idx >= this.trials.length) return this.practice ? this.endPractice(now) : this.showResult();
    this.show('');
    this.msg.setVisible(false);
    stopSpeech();
    this.phase = 'gap';
    this.until = now + 600 + Math.random() * 300;
  }

  private showResult() {
    this.phase = 'result';
    const s = summarize(this.results);
    const session = {
      version: '0.3.0', date: new Date().toISOString(), cfg: this.cfg, thresholds: this.thr,
      levels: { fairyMs: this.fairy.value, enemyMs: this.enemy.value }, summary: s, trials: this.results,
    };
    this.show('🏆');
    this.say([
      `Défis : ${s.fairies - s.omissions - s.wrongArms}/${s.fairies} · mauvais gestes : ${s.wrongArms}`,
      `Statues : ${s.enemies - s.falseAlarms}/${s.enemies}`,
      `Réaction : ${s.rtMeanMs} ms (±${s.rtSdMs})`,
      `Début / milieu / fin : ${s.thirds.join(' / ')} %`,
      `Arrêt : ${s.stopMeanMs ?? '–'} ms · agitation : ${s.agitation}`,
      '',
      '[ Copier le résultat ]',
    ].join('\n'));
    this.msg.setFontSize('30px').setY(420).setInteractive()
      .on('pointerdown', () => { void navigator.clipboard.writeText(JSON.stringify(session, null, 2)); });
    this.sendSummary(false);
  }

  /** SensAI : arrêt demandé par l'enfant ou le parent (bouton « J'ai mal / Stop »). */
  private stopEarly() {
    if (this.sent) return;
    this.phase = 'result';
    stopSpeech();
    this.show('🛑');
    this.say('Séance arrêtée. Repose-toi bien !');
    this.sendSummary(true);
  }

  /** SensAI : résumé de la séance envoyé à la page, qui l'enregistre pour l'ergothérapeute. */
  private sendSummary(stoppedEarly: boolean) {
    if (this.sent) return;
    this.sent = true;
    onStopRequest(null);
    const real = this.practice ? [] : this.results;
    const s = summarize(real);
    const goOk = s.fairies - s.omissions - s.wrongArms;
    const nogoOk = s.enemies - s.falseAlarms;
    const done = real.length;
    const target = this.practice ? this.cfg.n : this.trials.length;
    const pct = (a: number, b: number) => (b ? Math.round((1000 * a) / b) / 10 : 0);
    // Pas d'essai de ce type joué (arrêt pendant l'entraînement) : pas de taux, pour ne pas fausser le suivi
    const rate = (a: number, b: number) => (b ? pct(a, b) : null);
    const third = (i: number) => (done >= 6 ? s.thirds[i] : null);
    const stream = this.video?.srcObject as MediaStream | null;
    stream?.getTracks().forEach((t) => t.stop());
    toPlatform({
      type: 'done',
      duration_sec: Math.max(1, Math.round((Date.now() - (this.startedAt || Date.now())) / 1000)),
      metrics: {
        score: Math.round(pct(goOk + nogoOk, done)),
        success_rate: pct(goOk + nogoOk, done),
        repetitions: done,
        repetitions_target: target,
        // niveau : plus l'ogre est fréquent, plus il faut se retenir (même règle que le dashboard)
        level_number: this.cfg.goRatio >= 0.85 ? 1 : this.cfg.goRatio >= 0.7 ? 2 : 3,
        exercise_name: 'Attention et contrôle des gestes (le château)',
        played_at: new Date().toISOString(),
        go_success_rate: rate(goOk, s.fairies),
        nogo_success_rate: rate(nogoOk, s.enemies),
        omissions: s.omissions,
        wrong_gestures: s.wrongArms,
        false_alarms: s.falseAlarms,
        go_trials: s.fairies,
        nogo_trials: s.enemies,
        rt_mean_ms: s.rtMeanMs || null,
        rt_sd_ms: s.rtSdMs || null,
        stop_mean_ms: s.stopMeanMs,
        agitation: s.enemies ? s.agitation : null,
        accuracy_start: third(0),
        accuracy_middle: third(1),
        accuracy_end: third(2),
        gestures: this.cfg.kinds.join(','),
        go_ratio: this.cfg.goRatio,
        fairy_window_ms: this.fairy.value,
        enemy_window_ms: this.enemy.value,
        completed: !stoppedEarly && !this.practice && done >= target,
        stopped_early: stoppedEarly,
        input_mode: 'camera',
        events: real.map((r, i) => ({
          i, kind: r.kind, ok: r.ok, rt_ms: r.rtMs ?? null, wrong: !!r.wrongArm,
          stop_ms: r.stopMs ?? null, agitation: r.agitation != null ? Math.round(r.agitation * 100) / 100 : null,
        })),
      },
    });
  }
}