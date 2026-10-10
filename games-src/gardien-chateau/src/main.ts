import Phaser from 'phaser';
import { IntroScene } from './game/IntroScene';
import { MainScene } from './game/MainScene';

new Phaser.Game({
  type: Phaser.AUTO,
  parent: 'game',
  transparent: true,
  width: 1280,
  height: 720,
  scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
  scene: [IntroScene, MainScene],
});