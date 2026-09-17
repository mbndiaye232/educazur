/**
 * /admin/demandes — consultation des demandes d'inscription.
 *
 * Page protégée par authentification HTTP Basic, vérifiée côté serveur.
 * Liaisons attendues sur le projet Cloudflare Pages :
 *   DB              base D1
 *   ADMIN_USER      identifiant (variable)
 *   ADMIN_PASSWORD  mot de passe (secret)
 */

const REALM = 'Demandes d\'inscription — Educazur';
const PAR_PAGE = 100;

const entetesHtml = {
  'Content-Type': 'text/html; charset=utf-8',
  'Cache-Control': 'no-store',
  'X-Robots-Tag': 'noindex, nofollow',
  'Referrer-Policy': 'no-referrer',
};

function demandeAuth() {
  return new Response('Authentification requise.', {
    status: 401,
    headers: {
      'WWW-Authenticate': `Basic realm="${REALM}", charset="UTF-8"`,
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'no-store',
    },
  });
}

/** Comparaison à temps constant, pour ne rien laisser fuir par la durée. */
function memeChaine(a, b) {
  const ab = new TextEncoder().encode(a);
  const bb = new TextEncoder().encode(b);
  if (ab.length !== bb.length) return false;
  let diff = 0;
  for (let i = 0; i < ab.length; i += 1) diff |= ab[i] ^ bb[i];
  return diff === 0;
}

function autorise(request, env) {
  if (!env.ADMIN_USER || !env.ADMIN_PASSWORD) return false;

  const entete = request.headers.get('Authorization') || '';
  if (!entete.startsWith('Basic ')) return false;

  let decode;
  try {
    const binaire = atob(entete.slice(6));
    const octets = Uint8Array.from(binaire, (c) => c.charCodeAt(0));
    decode = new TextDecoder().decode(octets);
  } catch {
    return false;
  }

  const sep = decode.indexOf(':');
  if (sep < 0) return false;

  return memeChaine(decode.slice(0, sep), env.ADMIN_USER)
    && memeChaine(decode.slice(sep + 1), env.ADMIN_PASSWORD);
}

/** Échappe tout ce qui vient de la base avant insertion dans la page. */
function ech(valeur) {
  if (valeur === null || valeur === undefined) return '';
  return String(valeur)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function dateLisible(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return ech(iso);
  const p = (n) => String(n).padStart(2, '0');
  return `${p(d.getUTCDate())}/${p(d.getUTCMonth() + 1)}/${d.getUTCFullYear()}`
    + ` à ${p(d.getUTCHours())}h${p(d.getUTCMinutes())}`;
}

function page({ lignes, aTraiter, total, filtre }) {
  const rangs = lignes.map((d) => `
      <tr${d.traite ? ' class="est-traite"' : ''}>
        <td class="col-date">${dateLisible(d.recu_le)}</td>
        <td>
          <strong>${ech(d.parent)}</strong><br>
          <a href="tel:${ech(d.telephone.replace(/[^\d+]/g, ''))}">${ech(d.telephone)}</a>
          ${d.email ? `<br><a href="mailto:${ech(d.email)}">${ech(d.email)}</a>` : ''}
        </td>
        <td>${d.eleve ? ech(d.eleve) : '<span class="vide">—</span>'}</td>
        <td><span class="niveau">${ech(d.niveau)}</span></td>
        <td class="col-message">${d.message ? ech(d.message) : '<span class="vide">—</span>'}</td>
        <td class="col-action">
          <form method="post">
            <input type="hidden" name="id" value="${d.id}">
            <input type="hidden" name="traite" value="${d.traite ? 0 : 1}">
            <button type="submit" class="bouton ${d.traite ? 'bouton--rouvrir' : 'bouton--traiter'}">
              ${d.traite ? 'Rouvrir' : 'Marquer traitée'}
            </button>
          </form>
        </td>
      </tr>`).join('');

  return `<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Demandes d'inscription — Educazur</title>
<link rel="icon" href="/favicon.ico" sizes="any">
<style>
  :root { --navy:#0a2a5e; --blue:#0058ba; --red:#d81e2f; --line:#e3e7ee;
          --ink:#121b2e; --ink-600:#47526b; --sand:#f7f3ea; }
  * { box-sizing:border-box; }
  body { margin:0; font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
         color:var(--ink); background:#f6f8fb; }
  header { background:var(--navy); color:#fff; padding:1.3rem clamp(1rem,4vw,2.5rem); }
  header h1 { margin:0; font-size:1.3rem; font-weight:600; }
  header p { margin:.3rem 0 0; font-size:.86rem; color:rgba(255,255,255,.7); }
  header a { color:#9dc4f5; }
  main { padding:clamp(1rem,3vw,2rem); max-width:1400px; margin:0 auto; }
  .barre { display:flex; flex-wrap:wrap; gap:.6rem; align-items:center; margin-bottom:1.2rem; }
  .puce { padding:.4rem .9rem; border:1px solid var(--line); border-radius:999px;
          background:#fff; color:var(--ink-600); font-size:.86rem; text-decoration:none; }
  .puce--actif { background:var(--navy); border-color:var(--navy); color:#fff; font-weight:600; }
  .compteur { margin-left:auto; font-size:.86rem; color:var(--ink-600); }
  .compteur b { color:var(--red); }
  .cadre { background:#fff; border:1px solid var(--line); border-radius:12px; overflow:hidden; }
  .defile { overflow-x:auto; }
  table { width:100%; border-collapse:collapse; font-size:.9rem; min-width:900px; }
  th { text-align:left; padding:.8rem 1rem; background:#f2f7fd; color:var(--ink-600);
       font-size:.72rem; letter-spacing:.1em; text-transform:uppercase; border-bottom:1px solid var(--line); }
  td { padding:.85rem 1rem; border-bottom:1px solid var(--line); vertical-align:top; }
  tr:last-child td { border-bottom:0; }
  tr.est-traite { background:var(--sand); color:var(--ink-600); }
  tr.est-traite strong { font-weight:500; }
  .col-date { white-space:nowrap; color:var(--ink-600); font-variant-numeric:tabular-nums; }
  .col-message { max-width:30ch; white-space:pre-wrap; }
  .col-action { text-align:right; }
  .niveau { display:inline-block; padding:.2rem .6rem; border-radius:999px;
            background:#e6effb; color:var(--blue); font-weight:600; font-size:.82rem; white-space:nowrap; }
  .vide { color:#a6aebd; }
  a { color:var(--blue); }
  .bouton { padding:.45rem .85rem; border:1px solid var(--line); border-radius:8px;
            background:#fff; font:inherit; font-size:.82rem; font-weight:600; cursor:pointer; white-space:nowrap; }
  .bouton--traiter { border-color:var(--blue); color:var(--blue); }
  .bouton--traiter:hover { background:var(--blue); color:#fff; }
  .bouton--rouvrir { color:var(--ink-600); }
  .bouton--rouvrir:hover { border-color:var(--ink-600); }
  .rien { padding:3.5rem 1rem; text-align:center; color:var(--ink-600); }
  footer { padding:1.5rem clamp(1rem,4vw,2.5rem); font-size:.8rem; color:var(--ink-600); }
</style>
</head>
<body>

<header>
  <h1>Demandes d'inscription</h1>
  <p>
    Groupe Scolaire Educazur — <a href="/index.html">retour au site</a>.
    Les données sont stockées dans votre base Cloudflare et ne sont transmises
    à aucun service externe.
  </p>
</header>

<main>
  <div class="barre">
    <a class="puce ${filtre === 'attente' ? 'puce--actif' : ''}" href="?filtre=attente">À traiter</a>
    <a class="puce ${filtre === 'tout' ? 'puce--actif' : ''}" href="?filtre=tout">Toutes</a>
    <span class="compteur"><b>${aTraiter}</b> à traiter sur ${total} demande${total > 1 ? 's' : ''}</span>
  </div>

  <div class="cadre">
    ${lignes.length === 0 ? `
    <p class="rien">${filtre === 'attente'
      ? 'Aucune demande en attente. Tout est traité.'
      : 'Aucune demande enregistrée pour le moment.'}</p>` : `
    <div class="defile">
      <table>
        <thead>
          <tr>
            <th>Reçue le</th>
            <th>Parent</th>
            <th>Élève</th>
            <th>Niveau</th>
            <th>Message</th>
            <th></th>
          </tr>
        </thead>
        <tbody>${rangs}
        </tbody>
      </table>
    </div>`}
  </div>
</main>

<footer>
  ${lignes.length >= PAR_PAGE
    ? `Seules les ${PAR_PAGE} demandes les plus récentes sont affichées.`
    : 'Page privée, non indexée par les moteurs de recherche.'}
</footer>

</body>
</html>`;
}

async function rendre(env, url) {
  const filtre = url.searchParams.get('filtre') === 'tout' ? 'tout' : 'attente';

  const condition = filtre === 'attente' ? 'WHERE traite = 0' : '';
  const { results: lignes } = await env.DB.prepare(
    `SELECT id, recu_le, parent, telephone, email, eleve, niveau, message, traite
       FROM demandes ${condition}
      ORDER BY recu_le DESC
      LIMIT ${PAR_PAGE}`
  ).all();

  const { results: compte } = await env.DB.prepare(
    'SELECT COUNT(*) AS total, SUM(CASE WHEN traite = 0 THEN 1 ELSE 0 END) AS attente FROM demandes'
  ).all();

  return new Response(page({
    lignes: lignes || [],
    total: compte?.[0]?.total ?? 0,
    aTraiter: compte?.[0]?.attente ?? 0,
    filtre,
  }), { headers: entetesHtml });
}

function baseAbsente() {
  return new Response(
    '<!DOCTYPE html><html lang="fr"><meta charset="utf-8">'
    + '<title>Base non configurée</title>'
    + '<body style="font:16px/1.6 system-ui;max-width:42rem;margin:4rem auto;padding:0 1rem">'
    + "<h1>Base non configurée</h1><p>La liaison D1 nommée <code>DB</code> n'est pas "
    + 'attachée à ce projet Cloudflare Pages. Voir la section « Formulaire » du '
    + 'fichier <code>README.md</code>.</p>',
    { status: 503, headers: entetesHtml });
}

export async function onRequestGet({ request, env }) {
  if (!autorise(request, env)) return demandeAuth();
  if (!env.DB) return baseAbsente();
  return rendre(env, new URL(request.url));
}

export async function onRequestPost({ request, env }) {
  if (!autorise(request, env)) return demandeAuth();
  if (!env.DB) return baseAbsente();

  const donnees = await request.formData();
  const id = Number.parseInt(donnees.get('id'), 10);
  const traite = donnees.get('traite') === '1' ? 1 : 0;

  if (Number.isInteger(id)) {
    await env.DB.prepare('UPDATE demandes SET traite = ? WHERE id = ?')
      .bind(traite, id).run();
  }

  // redirection après POST, pour que le rechargement ne rejoue pas l'action
  const url = new URL(request.url);
  return new Response(null, {
    status: 303,
    headers: { Location: `${url.pathname}${url.search}`, 'Cache-Control': 'no-store' },
  });
}
