/* 404 — for unknown URLs (inside or outside the workspace). */
import { Button } from '../components/ui.jsx';

export default function NotFound({ inApp = false }) {
  return (
    <div className="container section center" style={{ maxWidth: 560 }}>
      <div className="eyebrow">Not found</div>
      <h1 className="display mt-3" style={{ fontSize: 48 }}>There’s nothing at this address.</h1>
      <p className="muted mt-3">The link may be from an older version of Hone. Everything is still here — just organised differently.</p>
      <div className="row mt-5" style={{ justifyContent: 'center' }}>
        <Button to="/">Go to the homepage</Button>
        {!inApp && <Button variant="secondary" to="/stocks/app">Open the workspace</Button>}
      </div>
    </div>
  );
}
