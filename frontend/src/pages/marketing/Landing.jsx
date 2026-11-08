/*
 * Landing — the site's front page ("/"). One job: explain Hone in plain
 * words and get interested people onto the waitlist.
 *
 * Deliberately plain: no scroll animations, glowing cards or live demos.
 * The product tools still exist (linked once, quietly, near the bottom) for
 * anyone who wants to look around.
 *
 * Layout, top to bottom:
 *   1. Header: logo + "Join the waitlist" (jumps to the form)
 *   2. Intro beside the waitlist form
 *   3. What the price is built on (three short columns)
 *   4. Who it's for
 *   5. Where things stand, then a second waitlist button
 *   6. Footer
 *
 * EDIT HERE: the copy lives in the constants just below.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Logo } from '../../components/SiteHeader.jsx';
import { ROLES, joinWaitlist, joinedEmail, validEmail, waitlistEnabled } from '../../lib/waitlist.js';
import { appPath, publicPath } from '../../lib/products.js';
import './landing.css';

const BASES = [
  {
    title: 'Weather where you are',
    body: 'Snow, rain, heat and frost records from the weather station nearest you, usually back to 1980, from USDA and NOAA.',
  },
  {
    title: 'What bad seasons have cost',
    body: 'How much a bad season takes out of revenue is measured from what ski resorts, park operators, contractors and farms have reported.',
  },
  {
    title: 'A price you can check',
    body: 'Every quote shows the seasons behind it, how often one went badly, and each assumption in the price.',
  },
];

const WHO = [
  'Ski resorts, ski schools and mountain-town shops',
  'Snow removal and plowing',
  'Outdoor venues, parks and events',
  'Construction, landscaping and trades',
  'HVAC contractors',
  'Orchards and farms',
];

export default function Landing() {
  return (
    <div className="landing">
      <a href="#main" className="skip-link">Skip to content</a>
      <header className="ld-header">
        <div className="container ld-header__inner">
          <Logo to="/" />
          <a href="#waitlist" className="btn btn--primary btn--sm">Join the waitlist</a>
        </div>
      </header>

      <main id="main">
        {/* 1. Intro + form */}
        <section className="ld-intro">
          <div className="container ld-intro__grid">
            <div>
              <h1 className="ld-title">Know what a bad season would cost you.</h1>
              <p className="ld-lede">
                Hone is for businesses and workers whose income depends on the weather. Tell it what you do, where, and
                roughly what you bring in. It works out how often a season goes badly where you are, what that would
                cost you, and what fair protection against it should cost.
              </p>
              <p className="ld-note">We’re opening Hone to a small group first.</p>
            </div>
            <WaitlistForm />
          </div>
        </section>

        {/* 2. What it's built on */}
        <section className="ld-section ld-section--alt" aria-labelledby="bases-title">
          <div className="container">
            <h2 id="bases-title" className="ld-h2">Built on records, not guesses</h2>
            <div className="ld-cols">
              {BASES.map(b => (
                <div key={b.title}>
                  <h3 className="ld-h3">{b.title}</h3>
                  <p className="ld-p">{b.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 3. Who it's for */}
        <section className="ld-section" aria-labelledby="who-title">
          <div className="container ld-split">
            <h2 id="who-title" className="ld-h2">Who it’s for</h2>
            <div>
              <ul className="ld-list">
                {WHO.map(w => <li key={w}>{w}</li>)}
              </ul>
              <p className="ld-p ld-muted">
                Anyone else whose year can be made or broken by one winter or one summer. Tell us about yours when you sign up.
              </p>
            </div>
          </div>
        </section>

        {/* 4. Honest status */}
        <section className="ld-section ld-section--alt" aria-labelledby="status-title">
          <div className="container ld-split">
            <h2 id="status-title" className="ld-h2">Where things stand</h2>
            <div>
              <p className="ld-p">
                Hone prices protection and explains the price. It doesn’t sell insurance or place trades. Selling cover is
                regulated, and we’re working out the right way to offer it. The waitlist tells us which businesses and
                places to start with.
              </p>
              <div className="ld-actions">
                <a href="#waitlist" className="btn btn--primary">Join the waitlist</a>
                <Link to={appPath('prediction-markets', 'quote')} className="ld-quiet-link">Or look at the early version</Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="ld-footer">
        <div className="container ld-footer__inner">
          <Logo to="/" />
          <nav className="ld-footer__links" aria-label="More">
            <Link to={publicPath('prediction-markets')}>Income hedging</Link>
            <Link to={publicPath('stocks')}>Stocks</Link>
            <Link to={publicPath('crypto')}>Crypto</Link>
            <Link to={publicPath('prediction-markets', 'methodology')}>Methodology</Link>
          </nav>
        </div>
        <div className="container">
          <p className="ld-fine">
            Hone is research software. Its prices and sizes are estimates to help you decide, not insurance or investment advice.
          </p>
        </div>
      </footer>
    </div>
  );
}

/* -------------------------------------------------------------- the form */
function WaitlistForm() {
  // If this browser already signed up, start on the thank-you state.
  const [done, setDone] = useState(() => (joinedEmail() ? 'already' : null));
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('');
  const [business, setBusiness] = useState('');
  // Bots fill every field; people never see this one (it's hidden by CSS).
  const [trap, setTrap] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const submit = async e => {
    e.preventDefault();
    setError(null);
    if (trap) { setDone('joined'); return; } // quietly drop bot sign-ups
    if (!validEmail(email)) { setError('Please enter a valid email address.'); return; }
    setBusy(true);
    try {
      setDone(await joinWaitlist({ email, role, business }));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="ld-form" id="waitlist">
      {done ? (
        <div role="status">
          <h2 className="ld-form__title">You’re on the list.</h2>
          <p className="ld-p">
            {done === 'already' ? 'This email was already signed up. ' : ''}
            We’ll email you when Hone is ready for your kind of business. Thanks for your interest.
          </p>
        </div>
      ) : (
        <form onSubmit={submit} noValidate>
          <h2 className="ld-form__title">Join the waitlist</h2>
          <label className="ld-label" htmlFor="wl-email">Email</label>
          <input id="wl-email" className="input" type="email" autoComplete="email" required
            value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />

          <label className="ld-label" htmlFor="wl-role">What describes you best</label>
          <select id="wl-role" className="input" value={role} onChange={e => setRole(e.target.value)}>
            <option value="">Choose one (optional)</option>
            {ROLES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
          </select>

          <label className="ld-label" htmlFor="wl-biz">Your business and where it is <span className="ld-muted">(optional)</span></label>
          <input id="wl-biz" className="input" type="text" maxLength={200}
            value={business} onChange={e => setBusiness(e.target.value)} placeholder="e.g. ski school in Taos, NM" />

          {/* Honeypot: hidden from people and screen readers. */}
          <input className="ld-trap" tabIndex={-1} aria-hidden="true" autoComplete="off"
            value={trap} onChange={e => setTrap(e.target.value)} name="company_website" />

          {error && <p className="ld-error" role="alert">{error}</p>}
          <button type="submit" className="btn btn--primary ld-submit" disabled={busy || !waitlistEnabled}>
            {busy ? 'Saving…' : 'Join the waitlist'}
          </button>
          <p className="ld-fine">
            {waitlistEnabled
              ? 'We’ll only use your email to tell you about Hone.'
              : 'Sign-ups aren’t switched on for this copy of the site.'}
          </p>
        </form>
      )}
    </div>
  );
}
