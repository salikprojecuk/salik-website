// Salik Project Admin - reads Netlify Form submissions server-side.
// Needs two environment variables in Netlify (Project configuration > Environment variables):
//   NETLIFY_API_TOKEN  - a Netlify personal access token
//   ADMIN_PASSWORD     - the password for the admin page
// SITE_ID is provided by Netlify automatically.
const crypto = require('crypto');

const API = 'https://api.netlify.com/api/v1';

const GROUPS = [
  { key: 'newsletter', label: 'Newsletter', forms: ['newsletter', 'newsletter-homepage', 'newsletter-footer', 'newsletter-signup'] },
  { key: 'support-family', label: 'Support: Family', forms: ['support-family'] },
  { key: 'support-individual', label: 'Support: Individual', forms: ['support-individual'] },
  { key: 'contact-form', label: 'Contact', forms: ['contact-form'] },
  { key: 'partner-enquiry', label: 'Partner enquiries', forms: ['partner-enquiry'] },
];

const HIDDEN_FIELDS = new Set(['form-name', 'bot-field', 'ip', 'user_agent', 'referrer']);

const sha = (s) => crypto.createHash('sha256').update(String(s)).digest();

const json = (status, body) => ({
  statusCode: status,
  headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex' },
  body: JSON.stringify(body),
});

async function api(path, token) {
  const res = await fetch(API + path, { headers: { Authorization: 'Bearer ' + token } });
  if (!res.ok) throw new Error('Netlify API ' + res.status + ' on ' + path.split('?')[0]);
  return res.json();
}

async function allSubmissions(formId, token) {
  const out = [];
  for (let page = 1; page <= 20; page++) {
    const batch = await api('/forms/' + formId + '/submissions?per_page=100&page=' + page, token);
    out.push(...batch);
    if (batch.length < 100) break;
  }
  return out;
}

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') return json(405, { error: 'Method not allowed' });

  const token = process.env.NETLIFY_API_TOKEN;
  const adminPassword = process.env.ADMIN_PASSWORD;
  const siteId = process.env.SITE_ID || process.env.NETLIFY_SITE_ID;
  if (!token || !adminPassword || !siteId) {
    return json(500, { error: 'Server not configured: missing NETLIFY_API_TOKEN, ADMIN_PASSWORD or SITE_ID.' });
  }

  let password = '';
  try { password = JSON.parse(event.body || '{}').password || ''; } catch (e) { /* ignore */ }
  if (!crypto.timingSafeEqual(sha(password), sha(adminPassword))) {
    await new Promise((r) => setTimeout(r, 800));
    return json(401, { error: 'Wrong password' });
  }

  try {
    const forms = await api('/sites/' + siteId + '/forms', token);
    const byName = Object.fromEntries(forms.map((f) => [f.name, f]));
    const groups = [];

    for (const g of GROUPS) {
      const items = [];
      for (const name of g.forms) {
        const form = byName[name];
        if (!form) continue;
        const subs = await allSubmissions(form.id, token);
        for (const s of subs) {
          const fields = {};
          for (const [k, v] of Object.entries(s.data || {})) {
            if (!HIDDEN_FIELDS.has(k) && v !== '') fields[k] = v;
          }
          items.push({
            id: s.id,
            form: name,
            created_at: s.created_at,
            name: s.name || s.first_name || fields.name || fields.full_name || '',
            email: s.email || fields.email || '',
            fields,
          });
        }
      }
      items.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      groups.push({ key: g.key, label: g.label, submissions: items });
    }
    return json(200, { groups, fetched_at: new Date().toISOString() });
  } catch (err) {
    return json(502, { error: err.message });
  }
};
