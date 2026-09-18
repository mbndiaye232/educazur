import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import '@fontsource/inter/500.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/700.css';
import '@fontsource/newsreader/500.css';
import '@fontsource/newsreader/400-italic.css';
import timeline from '../public/timeline.json';

// ---------------------------------------------------------------- charte
const NAVY = '#0a2a5e';
const NAVY_FONCE = '#071c3f';
const ROUGE = '#d81e2f';
const OR = '#ffd9a8';
const SERIF = '"Newsreader", Georgia, serif';
const SANS = '"Inter", "Segoe UI", Arial, sans-serif';

const FONDU = 18;          // durée d'un fondu enchaîné entre deux plans (images)

type Ligne = {
  texte: string;
  audio: string;
  debut: number;
  duree: number;
  images?: string[];
  chiffres?: string[][];
};
type Seq = {
  id: string;
  titre: string;
  debut: number;
  fin: number;
  lignes: Ligne[];
  images: string[];
};

const T = timeline as { fps: number; total: number; titre: string; sequences: Seq[] };
const f = (s: number) => Math.round(s * T.fps);
const seq = (id: string) => T.sequences.find((s) => s.id === id)!;

// ---------------------------------------------------------------- plans
type Plan = { src: string; debut: number; fin: number };

/** Découpe chaque séquence en plans : une image par tranche de temps. */
const construitPlans = (): Plan[] => {
  const plans: Plan[] = [];
  for (const s of T.sequences) {
    if (s.id === 'final') continue;
    const parLigne = s.lignes.some((l) => l.images);
    if (parLigne) {
      s.lignes.forEach((l, i) => {
        const fin = i + 1 < s.lignes.length ? s.lignes[i + 1].debut : s.fin;
        const debut = i === 0 ? s.debut : l.debut;
        const imgs = l.images ?? [];
        const pas = (fin - debut) / imgs.length;
        imgs.forEach((src, k) => plans.push({ src, debut: debut + k * pas, fin: debut + (k + 1) * pas }));
      });
    } else {
      const debut = s.id === 'titre' ? 0 : s.debut;
      const pas = (s.fin - debut) / s.images.length;
      s.images.forEach((src, k) => plans.push({ src, debut: debut + k * pas, fin: debut + (k + 1) * pas }));
    }
  }
  return plans;
};

const PLANS = construitPlans();

/** Image plein cadre avec léger zoom et glissement (effet « Ken Burns »). */
const PlanImage: React.FC<{ src: string; duree: number; sens: number; fondu: boolean }> = ({
  src, duree, sens, fondu,
}) => {
  const frame = useCurrentFrame();
  const p = Math.min(1, frame / Math.max(1, duree));
  const echelle = interpolate(p, [0, 1], [1.05, 1.15]);
  const x = interpolate(p, [0, 1], [-1.6 * sens, 1.6 * sens]);
  const opacite = fondu ? interpolate(frame, [0, FONDU], [0, 1], { extrapolateRight: 'clamp' }) : 1;
  return (
    <AbsoluteFill style={{ opacity: opacite, overflow: 'hidden', backgroundColor: NAVY_FONCE }}>
      <Img
        src={staticFile(src)}
        style={{
          width: '100%', height: '100%', objectFit: 'cover',
          transform: `scale(${echelle}) translateX(${x}%)`,
        }}
      />
      {/* voile bas pour la lisibilité des sous-titres */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(7,28,63,.35) 0%, rgba(7,28,63,0) 22%, rgba(7,28,63,0) 55%, rgba(7,28,63,.82) 100%)',
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- habillage
/** Sous-titre de la phrase en cours. */
const SousTitre: React.FC<{ texte: string; duree: number }> = ({ texte, duree }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 6, duree - 6, duree], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill style={{ justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 70 }}>
      <div
        style={{
          opacity: o, maxWidth: 1520, textAlign: 'center', color: 'white',
          fontFamily: SANS, fontWeight: 500, fontSize: 40, lineHeight: 1.4,
          textShadow: '0 2px 12px rgba(0,0,0,.55)',
        }}
      >
        {texte}
      </div>
    </AbsoluteFill>
  );
};

/** Étiquette de séquence en haut à gauche. */
const Etiquette: React.FC<{ titre: string; duree: number }> = ({ titre, duree }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [8, 22, duree - 12, duree], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const x = interpolate(frame, [8, 22], [-30, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <div
      style={{
        position: 'absolute', top: 64, left: 80, opacity: o, transform: `translateX(${x}px)`,
        display: 'flex', alignItems: 'center', gap: 18,
      }}
    >
      <div style={{ width: 44, height: 4, background: ROUGE, borderRadius: 2 }} />
      <div
        style={{
          fontFamily: SANS, fontWeight: 700, fontSize: 26, letterSpacing: '0.16em',
          textTransform: 'uppercase', color: 'white', textShadow: '0 2px 10px rgba(0,0,0,.5)',
        }}
      >
        {titre}
      </div>
    </div>
  );
};

/** Chiffres clés qui s'affichent pendant la phrase qui les cite. */
const Chiffres: React.FC<{ chiffres: string[][]; duree: number }> = ({ chiffres, duree }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sortie = interpolate(frame, [duree - 10, duree], [1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'flex-end', paddingRight: 110 }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 34, opacity: sortie }}>
        {chiffres.map(([valeur, legende], i) => {
          const s = spring({ frame: frame - 8 - i * 14, fps, config: { damping: 16 } });
          return (
            <div
              key={valeur}
              style={{
                transform: `translateX(${(1 - s) * 80}px)`, opacity: s,
                background: 'rgba(7,28,63,.78)', borderLeft: `6px solid ${i === 0 ? ROUGE : OR}`,
                padding: '22px 40px 24px 34px', borderRadius: 10, minWidth: 460,
              }}
            >
              <div style={{ fontFamily: SERIF, fontWeight: 500, fontSize: 112, lineHeight: 1, color: 'white' }}>
                {valeur}
              </div>
              <div
                style={{
                  marginTop: 10, fontFamily: SANS, fontWeight: 600, fontSize: 26,
                  letterSpacing: '0.06em', textTransform: 'uppercase', color: 'rgba(255,255,255,.78)',
                }}
              >
                {legende}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/** Petit logo permanent en haut à droite. */
const Signature: React.FC = () => (
  <Img
    src={staticFile('img/logo.png')}
    style={{ position: 'absolute', top: 48, right: 64, width: 96, height: 96, opacity: 0.92 }}
  />
);

/** Carton d'ouverture : logo et titre du reportage. */
const Ouverture: React.FC<{ duree: number }> = ({ duree }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const logo = spring({ frame, fps, config: { damping: 14 } });
  const titre = spring({ frame: frame - f(1.4), fps, config: { damping: 18 } });
  const sortie = interpolate(frame, [duree - 14, duree], [1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill
      style={{
        justifyContent: 'center', alignItems: 'center', opacity: sortie,
        background: 'radial-gradient(ellipse at center, rgba(7,28,63,.55) 0%, rgba(7,28,63,.88) 75%)',
      }}
    >
      <Img src={staticFile('img/logo.png')} style={{ width: 250, height: 250, transform: `scale(${logo})` }} />
      <div
        style={{
          marginTop: 44, opacity: titre, transform: `translateY(${(1 - titre) * 24}px)`,
          fontFamily: SERIF, fontStyle: 'italic', fontSize: 92, color: 'white', textAlign: 'center',
        }}
      >
        {T.titre}
      </div>
      <div
        style={{
          marginTop: 18, opacity: titre, fontFamily: SANS, fontWeight: 600, fontSize: 26,
          letterSpacing: '0.2em', textTransform: 'uppercase', color: OR,
        }}
      >
        Groupe Scolaire Educazur · Pikine
      </div>
    </AbsoluteFill>
  );
};

/** Écran final : chaque élément apparaît quand la voix le prononce. */
const Final: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = seq('final');
  const t0 = s.debut;
  const apparait = (t: number) => spring({ frame: frame - f(t - t0), fps, config: { damping: 18 } });
  const [nom, credo, rentree] = s.lignes;
  const a = apparait(nom.debut);
  const b = apparait(credo.debut);
  const c = apparait(rentree.debut);
  const d = apparait(rentree.debut + rentree.duree);
  const fond = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill
      style={{
        opacity: fond, justifyContent: 'center', alignItems: 'center', textAlign: 'center',
        background: `radial-gradient(ellipse at 50% 35%, #114289 0%, ${NAVY} 45%, ${NAVY_FONCE} 100%)`,
      }}
    >
      <Img src={staticFile('img/logo.png')} style={{ width: 200, height: 200, transform: `scale(${a})` }} />
      <div
        style={{
          marginTop: 36, opacity: a, fontFamily: SERIF, fontWeight: 500, fontSize: 96,
          color: 'white', letterSpacing: '-0.01em',
        }}
      >
        Groupe Scolaire Educazur
      </div>
      <div style={{ marginTop: 6, opacity: b, fontFamily: SERIF, fontStyle: 'italic', fontSize: 58, color: OR }}>
        L’excellence est notre credo
      </div>
      <div
        style={{
          marginTop: 54, opacity: c, transform: `scale(${0.9 + 0.1 * c})`,
          background: ROUGE, color: 'white', borderRadius: 999, padding: '20px 46px',
          fontFamily: SANS, fontWeight: 700, fontSize: 34,
        }}
      >
        Rentrée scolaire 2027 — Les inscriptions sont ouvertes
      </div>
      <div
        style={{
          marginTop: 40, opacity: d, fontFamily: SANS, fontWeight: 600, fontSize: 32,
          color: 'rgba(255,255,255,.88)', letterSpacing: '0.02em',
        }}
      >
        77 657 42 31 · 76 699 47 94 · 33 834 77 80
      </div>
      <div style={{ marginTop: 12, opacity: d, fontFamily: SANS, fontWeight: 500, fontSize: 26, color: 'rgba(255,255,255,.6)' }}>
        Km 16, Route de Rufisque — Pikine · educazur.pages.dev
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- montage
export const PubliReportage: React.FC = () => {
  const titre = seq('titre');
  const final = seq('final');
  const finalDebut = f(final.debut) - 6;

  return (
    <AbsoluteFill style={{ backgroundColor: NAVY_FONCE }}>
      {/* plans d'images, en fondu enchaîné */}
      {PLANS.map((p, i) => {
        const debut = Math.max(0, f(p.debut) - (i === 0 ? 0 : FONDU));
        const duree = f(p.fin) - debut + (i === PLANS.length - 1 ? 30 : 0);
        return (
          <Sequence key={i} from={debut} durationInFrames={duree}>
            <PlanImage src={p.src} duree={duree} sens={i % 2 === 0 ? 1 : -1} fondu={i > 0} />
          </Sequence>
        );
      })}

      {/* signature, hors ouverture et écran final */}
      <Sequence from={f(titre.fin)} durationInFrames={finalDebut - f(titre.fin)}>
        <Signature />
      </Sequence>

      {/* étiquettes de séquence */}
      {T.sequences.filter((s) => s.titre).map((s) => (
        <Sequence key={s.id} from={f(s.debut)} durationInFrames={f(s.fin) - f(s.debut)}>
          <Etiquette titre={s.titre} duree={f(s.fin) - f(s.debut)} />
        </Sequence>
      ))}

      {/* chiffres clés */}
      {T.sequences.flatMap((s) => s.lignes).filter((l) => l.chiffres).map((l) => {
        const duree = f(l.duree) + 18;
        return (
          <Sequence key={l.audio} from={f(l.debut)} durationInFrames={duree}>
            <Chiffres chiffres={l.chiffres!} duree={duree} />
          </Sequence>
        );
      })}

      {/* carton d'ouverture */}
      <Sequence from={0} durationInFrames={f(titre.fin)}>
        <Ouverture duree={f(titre.fin)} />
      </Sequence>

      {/* sous-titres, sauf sur l'ouverture et l'écran final qui affichent déjà le texte */}
      {T.sequences.filter((s) => s.id !== 'titre' && s.id !== 'final').flatMap((s) => s.lignes).map((l) => {
        const duree = f(l.duree) + 8;
        return (
          <Sequence key={'st' + l.audio} from={f(l.debut)} durationInFrames={duree}>
            <SousTitre texte={l.texte} duree={duree} />
          </Sequence>
        );
      })}

      {/* écran final */}
      <Sequence from={finalDebut}>
        <Final />
      </Sequence>

      {/* voix */}
      {T.sequences.flatMap((s) => s.lignes).map((l) => (
        <Sequence key={'a' + l.audio} from={f(l.debut)} durationInFrames={f(l.duree) + 6}>
          <Audio src={staticFile(l.audio)} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
