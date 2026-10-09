# SensAI — Frontend (Next.js)

## Lancer le site

```bash
npm install
cp .env.example .env.local   # Windows : Copy-Item .env.example .env.local
npm run dev
```

Le site est sur http://localhost:3000. Il a besoin du backend FastAPI démarré sur http://127.0.0.1:8000.

## Parcours connectés au backend

| Page | Rôle | Routes API utilisées |
|------|------|----------------------|
| `/register` | Création d’un compte thérapeute | `POST /auth/register`, `POST /auth/login` |
| `/login` | Connexion (thérapeute → `/therapist`, patient → `/dashboard`) | `POST /auth/login` |
| `/therapist` | Patients, diagnostic, jeux et réglages, code d’activation, séances | `/patients/`, `/games/`, `/patient-games/…`, `/sessions/…`, `/consultations/…`, `/activation-codes/` |
| `/activate` | Le patient crée ses identifiants avec le code du thérapeute | `POST /auth/activate` |
| `/dashboard` | Espace patient : jeux attribués, dernière séance, niveau | `/me/patient`, `/me/games`, `/me/sessions` |
| `/dashboard/game/le-hibou` | Jeu Le Hibou (caméra ou clavier), séance enregistrée à la fin | `GET /me/games`, `POST /me/sessions` |
| `/dashboard/game/gardien-lucioles` | Jeu Le Gardien des Lucioles de Maram (`public/games/gardien-lucioles/`, Phaser + MediaPipe Pose), réglages du thérapeute passés au jeu, séance enregistrée à la fin | `GET /me/games`, `POST /me/sessions` |

Le code d’accès à l’API est dans `lib/api.ts`, la présentation des jeux dans `lib/games.ts`.

---

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
